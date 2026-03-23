from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Subscription(Base):
    """CVE subscription model for user alerts"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cve_id = Column(String(50), ForeignKey("cves.id"), nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    cve = relationship("CVE", back_populates="subscriptions")
    
    # Composite index for unique subscriptions per user
    __table_args__ = (
        Index('idx_subscription_user_cve', 'user_id', 'cve_id', unique=True),
        Index('idx_subscription_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "cve_id": self.cve_id,
            "created_at": self.created_at.isoformat(),
        }
