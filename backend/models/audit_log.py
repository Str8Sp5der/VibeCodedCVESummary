from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class AuditLog(Base):
    """Audit logging model for security tracking"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    action = Column(String(100), index=True)  # e.g., "LOGIN", "CVE_SEARCH", "SUBSCRIBE"
    resource = Column(String(255), nullable=True)  # e.g., CVE ID
    
    method = Column(String(10))  # HTTP method: GET, POST, DELETE, etc.
    endpoint = Column(String(255))  # API endpoint
    
    status_code = Column(Integer)  # HTTP status code
    
    # Request details (sanitized, no sensitive data)
    request_params = Column(JSON, default=dict)
    response_status = Column(String(50))  # "success", "error", "unauthorized"
    
    ip_address = Column(String(50))
    user_agent = Column(String(500), nullable=True)
    
    error_message = Column(String(500), nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Foreign key relationship
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes for queries
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_endpoint_timestamp', 'endpoint', 'timestamp'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "method": self.method,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "response_status": self.response_status,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
        }
