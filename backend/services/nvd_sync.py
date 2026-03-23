import logging
import requests
import json
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.cve import CVE
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class NVDSyncService:
    """
    Service to sync CVE data from National Vulnerability Database (NVD)
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.nvd_url = settings.NVD_API_URL
        self.api_key = settings.NVD_API_KEY
        self.last_sync = None
        self.last_full_sync = None
        
    def _make_request(self, params: dict, retries: int = 3) -> dict:
        """
        Make request to NVD API with retry logic
        """
        if self.api_key:
            params['apiKey'] = self.api_key
        
        for attempt in range(retries):
            try:
                response = requests.get(
                    self.nvd_url,
                    params=params,
                    timeout=30,
                    headers={'User-Agent': 'CVE-Database-App/1.0'}
                )
                response.raise_for_status()
                
                # Rate limiting - respect NVD API limits
                time.sleep(1)
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.warning(f"NVD API error (attempt {attempt + 1}/{retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"NVD API failed after {retries} attempts: {e}")
                    raise
        
        return {}
    
    def _parse_nvd_cve(self, cve_item: dict) -> CVE:
        """
        Parse NVD CVE JSON and convert to CVE model
        """
        cve_data = cve_item.get('cve', {})
        cve_id = cve_data.get('id', '')
        
        # Extract description
        descriptions = cve_data.get('descriptions', [])
        description = descriptions[0].get('value', '') if descriptions else ''
        
        # Extract CVSS score
        metrics = cve_data.get('metrics', {})
        cvss_score = None
        cvss_vector = None
        
        # Try CVSS v3.1 first, then v3.0, then v2.0
        for metric_key in ['cvssMetricV31', 'cvssMetricV30', 'cvssMetricV20']:
            if metric_key in metrics:
                metric_data = metrics[metric_key][0] if metrics[metric_key] else {}
                cvss_data = metric_data.get('cvssData', {})
                cvss_score = cvss_data.get('baseScore')
                cvss_vector = cvss_data.get('vectorString')
                break
        
        # Extract CWE IDs
        cwe_ids = []
        weaknesses = cve_data.get('weaknesses', [])
        for weakness in weaknesses:
            cwe_list = weakness.get('description', [])
            for cwe_item in cwe_list:
                cwe_id = cwe_item.get('value')
                if cwe_id and cwe_id not in cwe_ids:
                    cwe_ids.append(cwe_id)
        
        # Extract vulnerable products/configurations
        vulnerable_products = []
        configs = cve_data.get('configurations', [])
        for config in configs:
            nodes = config.get('nodes', [])
            for node in nodes:
                cpematch = node.get('cpeMatch', [])
                for match in cpematch:
                    cpe = match.get('criteria')
                    if cpe and cpe not in vulnerable_products:
                        vulnerable_products.append(cpe)
        
        # Extract references
        references = []
        ref_data = cve_data.get('references', [])
        for ref in ref_data:
            url = ref.get('url')
            if url:
                references.append({
                    'url': url,
                    'source': ref.get('source'),
                    'tags': ref.get('tags', [])
                })
        
        # Parse dates
        published_date = cve_data.get('published')
        last_modified = cve_data.get('lastModified')
        
        if published_date:
            published_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
        if last_modified:
            last_modified = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
        
        return CVE(
            id=cve_id,
            description=description,
            cvss_score=cvss_score,
            cvss_vector=cvss_vector,
            cwe_ids=cwe_ids,
            published_date=published_date,
            last_modified_date=last_modified,
            vulnerable_products=vulnerable_products[:10],  # Limit to 10
            references=references,
            cache_updated_at=datetime.utcnow(),
        )
    
    def sync_recent_cves(self, hours: int = 1) -> dict:
        """
        Delta sync: Fetch CVEs modified in last N hours
        """
        logger.info(f"Starting delta sync for CVEs modified in last {hours} hours...")
        
        try:
            now = datetime.utcnow()
            since = now - timedelta(hours=hours + 1)  # Buffer for API delay
            
            params = {
                'lastModStartDate': since.isoformat() + 'Z',
                'lastModEndDate': now.isoformat() + 'Z',
                'resultsPerPage': 2000,
            }
            
            data = self._make_request(params)
            vulnerabilities = data.get('vulnerabilities', [])
            
            new_count = 0
            updated_count = 0
            
            for cve_item in vulnerabilities:
                cve_id = cve_item['cve']['id']
                
                # Check if CVE exists
                existing = self.db.query(CVE).filter_by(id=cve_id).first()
                
                try:
                    if existing:
                        # Update existing CVE
                        new_cve = self._parse_nvd_cve(cve_item)
                        existing.description = new_cve.description
                        existing.cvss_score = new_cve.cvss_score
                        existing.cvss_vector = new_cve.cvss_vector
                        existing.cwe_ids = new_cve.cwe_ids
                        existing.vulnerable_products = new_cve.vulnerable_products
                        existing.references = new_cve.references
                        existing.last_modified_date = new_cve.last_modified_date
                        existing.cache_updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Create new CVE
                        new_cve = self._parse_nvd_cve(cve_item)
                        self.db.add(new_cve)
                        new_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing CVE {cve_id}: {e}")
                    continue
            
            self.db.commit()
            self.last_sync = now
            
            logger.info(f"✓ Delta sync complete: {new_count} new, {updated_count} updated CVEs")
            
            return {
                'new': new_count,
                'updated': updated_count,
                'timestamp': now.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Delta sync failed: {e}")
            self.db.rollback()
            raise
    
    def sync_recent_cves_paginated(self, start_index: int = 0, batch_size: int = 2000) -> dict:
        """
        Fetch CVEs with pagination (for full sync or specific year range)
        """
        logger.info(f"Fetching CVE batch starting at index {start_index}...")
        
        try:
            params = {
                'startIndex': start_index,
                'resultsPerPage': batch_size,
            }
            
            data = self._make_request(params)
            vulnerabilities = data.get('vulnerabilities', [])
            total_results = data.get('totalResults', 0)
            
            new_count = 0
            updated_count = 0
            
            for cve_item in vulnerabilities:
                try:
                    cve_id = cve_item['cve']['id']
                    existing = self.db.query(CVE).filter_by(id=cve_id).first()
                    
                    if existing:
                        new_cve = self._parse_nvd_cve(cve_item)
                        existing.description = new_cve.description
                        existing.cvss_score = new_cve.cvss_score
                        existing.cvss_vector = new_cve.cvss_vector
                        existing.cwe_ids = new_cve.cwe_ids
                        existing.vulnerable_products = new_cve.vulnerable_products
                        existing.references = new_cve.references
                        existing.cache_updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        new_cve = self._parse_nvd_cve(cve_item)
                        self.db.add(new_cve)
                        new_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing CVE: {e}")
                    continue
            
            self.db.commit()
            
            has_more = (start_index + batch_size) < total_results
            
            return {
                'new': new_count,
                'updated': updated_count,
                'has_more': has_more,
                'next_index': start_index + batch_size if has_more else None,
                'total': total_results,
            }
            
        except Exception as e:
            logger.error(f"Pagination sync failed: {e}")
            self.db.rollback()
            raise
    
    def get_sync_status(self) -> dict:
        """
        Get current sync status
        """
        cve_count = self.db.query(CVE).count()
        latest_cve = self.db.query(CVE).order_by(CVE.published_date.desc()).first()
        
        return {
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'last_full_sync': self.last_full_sync.isoformat() if self.last_full_sync else None,
            'cve_count': cve_count,
            'latest_cve_date': latest_cve.published_date.isoformat() if latest_cve else None,
        }
