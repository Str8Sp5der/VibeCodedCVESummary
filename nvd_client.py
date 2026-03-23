"""
nvd_client.py — MITRE CVE API client + PoC scraping

Data sources:
  • MITRE CVE API  → CVE metadata, CVSS, affected systems
  • ExploitDB     → JSON search endpoint for known exploits
  • nomi-sec/PoC-in-GitHub → GitHub PoC index (raw JSON per CVE)
  • GitHub Advisory API   → supplemental advisory data
"""

import re
import time
import logging
import requests
import bleach
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)

NVD_BASE = "https://cveawg.mitre.org/api/cve"
EXPLOITDB_API  = "https://www.exploit-db.com/search"
POCGITHUB_RAW  = "https://raw.githubusercontent.com/nomi-sec/PoC-in-GitHub/master/{year}/{cve_id}.json"
GH_ADVISORY    = "https://api.github.com/advisories"

_SAFE_ATTRS: dict = {"a": ["href", "rel"], "code": []}


def _sanitize(text: str, max_len: int = 4000) -> str:
    """Strip all HTML tags except safe inline elements, cap length."""
    clean = bleach.clean(str(text), tags=list(_SAFE_ATTRS.keys()), attributes=_SAFE_ATTRS)
    return clean[:max_len]


class NVDClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        if api_key:
            self.session.headers["apiKey"] = api_key

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #
    def fetch_cve(self, cve_id: str) -> dict | None:
        """Fetch a single CVE from NVD, enrich with PoC data."""
        try:
            resp = self.session.get(
                f"{NVD_BASE}/{cve_id}", timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            log.error("NVD fetch failed for %s: %s", cve_id, exc)
            return None

        if not data:
            return None

        parsed = self._parse_mitre(data)

        # Enrich with PoC sources (failures are non-fatal)
        parsed["poc"] = self._collect_poc(cve_id)

        return parsed

    def update_recent_cves(self, db, days_back: int = 1) -> int:
        """Pull CVEs published/modified in the last N days into the local DB."""
        now   = datetime.now(timezone.utc)
        start = now - timedelta(days=days_back)
        fmt   = "%Y-%m-%dT%H:%M:%S.000"

        params = {
            "pubStartDate": start.strftime(fmt),
            "pubEndDate":   now.strftime(fmt),
            "resultsPerPage": 100,
        }
        try:
            resp = self.session.get(NVD_BASE, params=params, timeout=30)
            resp.raise_for_status()
            vulns = resp.json().get("vulnerabilities", [])
        except Exception as exc:
            log.error("NVD bulk fetch failed: %s", exc)
            db.log_update(0, success=False)
            return 0

        count = 0
        for v in vulns:
            try:
                parsed = self._parse_nvd(v["cve"])
                parsed["poc"] = self._collect_poc(parsed["id"])
                db.store_cve(parsed)
                count += 1
                time.sleep(0.05)          # polite delay
            except Exception as exc:
                log.warning("Skipped %s: %s", v.get("cve", {}).get("id"), exc)

        db.log_update(count, success=True)
        log.info("Auto-update: stored %d CVEs", count)
        return count

    # ------------------------------------------------------------------ #
    # NVD Parsing                                                          #
    # ------------------------------------------------------------------ #
    def _parse_nvd(self, cve: dict) -> dict:
        cve_id = cve.get("id", "")

        # --- Description (English preferred) ---
        descs = cve.get("descriptions", [])
        description = next(
            (d["value"] for d in descs if d.get("lang") == "en"),
            "No description available.",
        )

        # --- CVSS ---
        metrics  = cve.get("metrics", {})
        cvss_v3  = self._extract_cvssv3(metrics)
        cvss_v2  = self._extract_cvssv2(metrics)

        # --- Affected Systems (CPE) ---
        affected = self._extract_cpe(cve.get("configurations", []))

        # --- References ---
        refs = [
            {
                "url":    _sanitize(r["url"], 512),
                "source": _sanitize(r.get("source", ""), 64),
                "tags":   r.get("tags", []),
            }
            for r in cve.get("references", [])[:25]
        ]

        # --- CWE ---
        cwes = []
        for w in cve.get("weaknesses", []):
            for d in w.get("description", []):
                if d.get("lang") == "en":
                    cwes.append(d["value"])

        return {
            "id":               cve_id,
            "description":      _sanitize(description),
            "published":        cve.get("published", ""),
            "modified":         cve.get("lastModified", ""),
            "cvss_v3":          cvss_v3,
            "cvss_v2":          cvss_v2,
            "affected_systems": affected,
            "refs":             refs,
            "cwes":             cwes,
            "poc":              [],          # filled later
            "source":           "NVD",
            "fetched_at":       datetime.utcnow().isoformat(),
        }

    def _parse_nvd_html(self, soup, cve_id: str) -> dict:
        # Description
        desc_elem = soup.find("div", {"id": "cvedetails"})
        description = "No description available."
        if desc_elem:
            p = desc_elem.find("p")
            if p:
                description = p.text.strip()

        # Published and Modified
        published = ""
        modified = ""
        date_table = soup.find("table", {"class": "details"})
        if date_table:
            rows = date_table.find_all("tr")
            for row in rows:
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    if "Publish Date" in th.text:
                        published = td.text.strip()
                    elif "Update Date" in th.text:
                        modified = td.text.strip()

        # CVSS
        cvss_v3 = None
        cvss_v2 = None
        cvss_table = soup.find("table", {"id": "cvssscorestable"})
        if cvss_table:
            rows = cvss_table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    version = cells[0].text.strip()
                    score = cells[1].text.strip()
                    severity = cells[2].text.strip()
                    if "3.1" in version or "3.0" in version:
                        cvss_v3 = {
                            "score": float(score) if score else 0.0,
                            "severity": severity,
                            "vector": "",
                            "exploitability_score": None,
                            "impact_score": None,
                            "attack_vector": "",
                            "attack_complexity": "",
                            "privileges_required": "",
                            "user_interaction": "",
                            "scope": "",
                            "confidentiality_impact": "",
                            "integrity_impact": "",
                            "availability_impact": "",
                        }
                    elif "2.0" in version:
                        cvss_v2 = {
                            "score": float(score) if score else 0.0,
                            "severity": severity,
                            "vector": "",
                        }

        # Affected Systems
        affected = []
        vuln_prod_table = soup.find("table", {"id": "vulnprodstable"})
        if vuln_prod_table:
            rows = vuln_prod_table.find_all("tr")[1:]  # Skip header
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 4:
                    vendor = cells[0].text.strip()
                    product = cells[1].text.strip()
                    version = cells[2].text.strip()
                    affected.append({
                        "vendor": vendor,
                        "product": product,
                        "version": version,
                        "version_start": "",
                        "version_end": "",
                        "cpe": "",
                    })

        # References
        refs = []
        ref_table = soup.find("table", {"id": "referenceslist"})
        if ref_table:
            rows = ref_table.find_all("tr")[1:]
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    url_elem = cells[0].find("a")
                    url = url_elem["href"] if url_elem else ""
                    source = cells[1].text.strip()
                    refs.append({
                        "url": _sanitize(url, 512),
                        "source": _sanitize(source, 64),
                        "tags": [],
                    })

        # CWE
        cwes = []
        cwe_elem = soup.find("table", {"id": "cwetable"})
        if cwe_elem:
            rows = cwe_elem.find_all("tr")[1:]
            for row in rows:
                cells = row.find_all("td")
                if cells:
                    cwe_link = cells[0].find("a")
                    if cwe_link:
                        cwes.append(cwe_link.text.strip())

        return {
            "id":               cve_id,
            "description":      _sanitize(description),
            "published":        published,
            "modified":         modified,
            "cvss_v3":          cvss_v3,
            "cvss_v2":          cvss_v2,
            "affected_systems": affected,
            "refs":             refs,
            "cwes":             cwes,
            "poc":              [],          # filled later
            "source":           "CVE Details",
            "fetched_at":       datetime.utcnow().isoformat(),
        }

    def _parse_mitre(self, data: dict) -> dict:
        cve_id = data.get("cveMetadata", {}).get("cveId", "")

        containers = data.get("containers", {})
        cna = containers.get("cna", {})

        # Description
        descriptions = cna.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            "No description available.",
        )

        # Published and Modified
        published = data.get("cveMetadata", {}).get("datePublished", "")
        modified = data.get("cveMetadata", {}).get("dateUpdated", "")

        # CVSS
        metrics = cna.get("metrics", [])
        cvss_v3 = None
        cvss_v2 = None
        for metric in metrics:
            if "cvssV3_1" in metric:
                cvss = metric["cvssV3_1"]
                cvss_v3 = {
                    "score": cvss.get("baseScore"),
                    "severity": cvss.get("baseSeverity", "UNKNOWN"),
                    "vector": cvss.get("vectorString", ""),
                    "exploitability_score": None,
                    "impact_score": None,
                    "attack_vector": cvss.get("attackVector"),
                    "attack_complexity": cvss.get("attackComplexity"),
                    "privileges_required": cvss.get("privilegesRequired"),
                    "user_interaction": cvss.get("userInteraction"),
                    "scope": cvss.get("scope"),
                    "confidentiality_impact": cvss.get("confidentialityImpact"),
                    "integrity_impact": cvss.get("integrityImpact"),
                    "availability_impact": cvss.get("availabilityImpact"),
                }
            elif "cvssV3_0" in metric:
                cvss = metric["cvssV3_0"]
                cvss_v3 = {
                    "score": cvss.get("baseScore"),
                    "severity": cvss.get("baseSeverity", "UNKNOWN"),
                    "vector": cvss.get("vectorString", ""),
                    "exploitability_score": None,
                    "impact_score": None,
                    "attack_vector": cvss.get("attackVector"),
                    "attack_complexity": cvss.get("attackComplexity"),
                    "privileges_required": cvss.get("privilegesRequired"),
                    "user_interaction": cvss.get("userInteraction"),
                    "scope": cvss.get("scope"),
                    "confidentiality_impact": cvss.get("confidentialityImpact"),
                    "integrity_impact": cvss.get("integrityImpact"),
                    "availability_impact": cvss.get("availabilityImpact"),
                }
            elif "cvssV2_0" in metric:
                cvss = metric["cvssV2_0"]
                cvss_v2 = {
                    "score": cvss.get("baseScore"),
                    "severity": cvss.get("severity", "UNKNOWN"),
                    "vector": cvss.get("vectorString", ""),
                }

        # Affected Systems
        affected = []
        for aff in cna.get("affected", []):
            vendor = aff.get("vendor", "")
            product = aff.get("product", "")
            versions = aff.get("versions", [])
            for ver in versions:
                affected.append({
                    "vendor": vendor,
                    "product": product,
                    "version": ver.get("version", ""),
                    "version_start": "",
                    "version_end": "",
                    "cpe": "",
                })

        # References
        refs = []
        for ref in cna.get("references", []):
            refs.append({
                "url": _sanitize(ref.get("url", ""), 512),
                "source": "",
                "tags": ref.get("tags", []),
            })

        # CWE
        cwes = []
        for problem in cna.get("problemTypes", []):
            for desc in problem.get("descriptions", []):
                if desc.get("lang") == "en":
                    cwes.append(desc.get("description", ""))

        return {
            "id":               cve_id,
            "description":      _sanitize(description),
            "published":        published,
            "modified":         modified,
            "cvss_v3":          cvss_v3,
            "cvss_v2":          cvss_v2,
            "affected_systems": affected,
            "refs":             refs,
            "cwes":             cwes,
            "poc":              [],          # filled later
            "source":           "MITRE",
            "fetched_at":       datetime.utcnow().isoformat(),
        }

    def _parse_github(self, advisory: dict) -> dict:
        cve_id = advisory.get("cve_id", "")

        # Description
        description = advisory.get("description", "No description available.")

        # Published and Modified
        published = advisory.get("published_at", "")
        modified = advisory.get("updated_at", "")

        # CVSS
        cvss_v3 = None
        cvss_v2 = None
        cvss = advisory.get("cvss", {})
        if cvss:
            score = cvss.get("score", 0.0)
            vector = cvss.get("vector_string", "")
            severity = cvss.get("severity", "UNKNOWN")
            cvss_v3 = {
                "score": score,
                "severity": severity,
                "vector": vector,
                "exploitability_score": None,
                "impact_score": None,
                "attack_vector": "",
                "attack_complexity": "",
                "privileges_required": "",
                "user_interaction": "",
                "scope": "",
                "confidentiality_impact": "",
                "integrity_impact": "",
                "availability_impact": "",
            }

        # Affected Systems
        affected = []
        for vuln in advisory.get("vulnerabilities", []):
            package = vuln.get("package", {})
            affected.append({
                "vendor": package.get("ecosystem", ""),
                "product": package.get("name", ""),
                "version": vuln.get("vulnerable_version_range", ""),
                "version_start": "",
                "version_end": "",
                "cpe": "",
            })

        # References
        refs = []
        for ref in advisory.get("references", []):
            if isinstance(ref, str):
                refs.append({
                    "url": _sanitize(ref, 512),
                    "source": "",
                    "tags": [],
                })
            else:
                refs.append({
                    "url": _sanitize(ref.get("url", ""), 512),
                    "source": "",
                    "tags": [],
                })

        # CWE
        cwes = advisory.get("cwes", [])

        return {
            "id":               cve_id,
            "description":      _sanitize(description),
            "published":        published,
            "modified":         modified,
            "cvss_v3":          cvss_v3,
            "cvss_v2":          cvss_v2,
            "affected_systems": affected,
            "refs":             refs,
            "cwes":             cwes,
            "poc":              [],          # filled later
            "source":           "GitHub Advisories",
            "fetched_at":       datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _extract_cvssv3(metrics: dict) -> dict | None:
        for key in ("cvssMetricV31", "cvssMetricV30"):
            if key in metrics:
                m  = metrics[key][0]
                cd = m["cvssData"]
                return {
                    "score":                  cd.get("baseScore"),
                    "severity":               cd.get("baseSeverity", "UNKNOWN"),
                    "vector":                 cd.get("vectorString", ""),
                    "exploitability_score":   m.get("exploitabilityScore"),
                    "impact_score":           m.get("impactScore"),
                    "attack_vector":          cd.get("attackVector"),
                    "attack_complexity":      cd.get("attackComplexity"),
                    "privileges_required":    cd.get("privilegesRequired"),
                    "user_interaction":       cd.get("userInteraction"),
                    "scope":                  cd.get("scope"),
                    "confidentiality_impact": cd.get("confidentialityImpact"),
                    "integrity_impact":       cd.get("integrityImpact"),
                    "availability_impact":    cd.get("availabilityImpact"),
                }
        return None

    @staticmethod
    def _extract_cvssv2(metrics: dict) -> dict | None:
        if "cvssMetricV2" in metrics:
            m  = metrics["cvssMetricV2"][0]
            cd = m["cvssData"]
            return {
                "score":    cd.get("baseScore"),
                "severity": m.get("baseSeverity", "UNKNOWN"),
                "vector":   cd.get("vectorString", ""),
            }
        return None

    @staticmethod
    def _extract_cpe(configurations: list) -> list[dict]:
        systems, seen = [], set()
        for cfg in configurations:
            for node in cfg.get("nodes", []):
                for match in node.get("cpeMatch", []):
                    if not match.get("vulnerable", False):
                        continue
                    cpe   = match.get("criteria", "")
                    parts = cpe.split(":")
                    if len(parts) < 6:
                        continue
                    vendor, product, version = parts[3], parts[4], parts[5]
                    key = f"{vendor}:{product}"
                    if key in seen:
                        continue
                    seen.add(key)
                    systems.append(
                        {
                            "vendor":        vendor.replace("_", " ").title(),
                            "product":       product.replace("_", " ").title(),
                            "version":       version if version != "*" else "All versions",
                            "version_start": match.get("versionStartIncluding")
                                             or match.get("versionStartExcluding"),
                            "version_end":   match.get("versionEndIncluding")
                                             or match.get("versionEndExcluding"),
                            "cpe":           cpe,
                        }
                    )
                    if len(systems) >= 40:
                        return systems
        return systems

    # ------------------------------------------------------------------ #
    # PoC Aggregation                                                      #
    # ------------------------------------------------------------------ #
    def _collect_poc(self, cve_id: str) -> list[dict]:
        poc: list[dict] = []
        poc.extend(self._exploitdb_search(cve_id))
        poc.extend(self._github_poc_index(cve_id))
        return poc[:15]                   # cap total PoCs returned

    def _exploitdb_search(self, cve_id: str) -> list[dict]:
        """Query ExploitDB JSON search endpoint."""
        results = []
        # ExploitDB expects the numeric portion only
        num = re.sub(r"(?i)^CVE-", "", cve_id)
        try:
            resp = self.session.get(
                EXPLOITDB_API,
                params={"cve": num, "type": "", "platform": ""},
                headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"},
                timeout=8,
            )
            if resp.status_code == 200:
                for item in resp.json().get("data", [])[:6]:
                    eid = item.get("id", "")
                    results.append(
                        {
                            "title":    _sanitize(item.get("description", "No title"), 200),
                            "url":      f"https://www.exploit-db.com/exploits/{eid}",
                            "type":     _sanitize(
                                (item.get("type") or {}).get("name", "Unknown")
                                if isinstance(item.get("type"), dict)
                                else str(item.get("type", "Unknown")),
                                64,
                            ),
                            "platform": _sanitize(
                                (item.get("platform") or {}).get("name", "Unknown")
                                if isinstance(item.get("platform"), dict)
                                else str(item.get("platform", "Unknown")),
                                64,
                            ),
                            "author":   _sanitize(
                                (item.get("author") or {}).get("name", "Unknown")
                                if isinstance(item.get("author"), dict)
                                else str(item.get("author", "Unknown")),
                                64,
                            ),
                            "date":     item.get("date_published", ""),
                            "source":   "ExploitDB",
                        }
                    )
        except Exception as exc:
            log.debug("ExploitDB query failed for %s: %s", cve_id, exc)
        return results

    def _github_poc_index(self, cve_id: str) -> list[dict]:
        """Check nomi-sec/PoC-in-GitHub raw JSON index."""
        results = []
        # Extract year from CVE-YYYY-NNNNN
        m = re.match(r"(?i)CVE-(\d{4})-\d+", cve_id)
        if not m:
            return results
        year = m.group(1)
        url  = POCGITHUB_RAW.format(year=year, cve_id=cve_id.upper())
        try:
            resp = self.session.get(url, timeout=6)
            if resp.status_code == 200:
                for entry in resp.json()[:8]:
                    results.append(
                        {
                            "title":       _sanitize(entry.get("name", "GitHub PoC"), 200),
                            "url":         _sanitize(entry.get("html_url", ""), 512),
                            "description": _sanitize(entry.get("description", ""), 300),
                            "stars":       entry.get("stargazers_count", 0),
                            "date":        entry.get("created_at", ""),
                            "source":      "GitHub",
                        }
                    )
        except Exception as exc:
            log.debug("PoC-in-GitHub lookup failed for %s: %s", cve_id, exc)
        return results
