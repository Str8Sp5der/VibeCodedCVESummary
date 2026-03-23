from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import json


class CVE(Base):
    """CVE database model"""
    __tablename__ = "cves"
    
    id = Column(String(50), primary_key=True, index=True)  # CVE-YYYY-NNNN
    description = Column(Text, nullable=True)
    cvss_score = Column(Float, nullable=True, index=True)
    cvss_vector = Column(String(100), nullable=True)
    cwe_ids = Column(JSON, default=list)  # List of CWE IDs
    
    published_date = Column(DateTime, nullable=True, index=True)
    last_modified_date = Column(DateTime, nullable=True)
    
    # Vulnerable products/systems
    vulnerable_products = Column(JSON, default=list)  # List of affected products
    
    # References to external resources
    references = Column(JSON, default=list)
    
    # Proof of Concept info
    has_poc = Column(Boolean, default=False, index=True)
    poc_code = Column(Text, nullable=True)  # Encrypted
    poc_source = Column(String(255), nullable=True)  # URL/source of PoC
    poc_language = Column(String(50), nullable=True)  # Language hint for syntax highlighting
    
    # Metadata
    cache_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="cve", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_cve_cvss_score', 'cvss_score'),
        Index('idx_cve_published_date', 'published_date'),
        Index('idx_cve_has_poc', 'has_poc'),
    )
    
    def to_dict(self, include_poc: bool = False):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "description": self.description,
            "cvss_score": self.cvss_score,
            "cvss_vector": self.cvss_vector,
            "cwe_ids": self.cwe_ids or [],
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "last_modified_date": self.last_modified_date.isoformat() if self.last_modified_date else None,
            "vulnerable_products": self.vulnerable_products or [],
            "references": self.references or [],
            "has_poc": self.has_poc,
            "poc_source": self.poc_source,
            "cache_updated_at": self.cache_updated_at.isoformat() if self.cache_updated_at else None,
        }
        
        if include_poc and self.has_poc:
            data["poc_code"] = self.poc_code
            data["poc_language"] = self.poc_language
        
        return data
