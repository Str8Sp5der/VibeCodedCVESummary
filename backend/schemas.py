from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ========== Request Schemas ==========

class UserRegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
                "full_name": "John Doe"
            }
        }


class UserLoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!"
            }
        }


class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


# ========== Response Schemas ==========

class UserResponse(BaseModel):
    """User data response"""
    id: int
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # in seconds


class AuthResponse(BaseModel):
    """Complete authentication response"""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CSRFTokenResponse(BaseModel):
    """CSRF token response"""
    csrf_token: str


# ========== CVE Schemas ==========

class CVESearchRequest(BaseModel):
    """CVE search request"""
    q: Optional[str] = Field(None, description="Search query")
    severity: Optional[str] = Field(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)")
    year: Optional[int] = Field(None, description="Filter by year")
    page: int = Field(1, ge=1, description="Page number for pagination")
    limit: int = Field(50, ge=1, le=100, description="Results per page")

    class Config:
        json_schema_extra = {
            "example": {
                "q": "RCE vulnerability",
                "severity": "CRITICAL",
                "page": 1,
                "limit": 50
            }
        }


class CVEResponse(BaseModel):
    """CVE data response"""
    id: str
    description: Optional[str]
    cvss_score: Optional[float]
    cvss_vector: Optional[str]
    cwe_ids: list = []
    published_date: Optional[str]
    last_modified_date: Optional[str]
    vulnerable_products: list = []
    references: list = []
    has_poc: bool
    poc_source: Optional[str]
    cache_updated_at: Optional[str]

    class Config:
        from_attributes = True


class CVEDetailResponse(CVEResponse):
    """Detailed CVE response with PoC code"""
    poc_code: Optional[str] = None
    poc_language: Optional[str] = None

    class Config:
        from_attributes = True


class CVESearchResponse(BaseModel):
    """CVE search results response"""
    total: int
    items: list[CVEResponse]
    page: int
    limit: int
    total_pages: int


class SubscriptionRequest(BaseModel):
    """CVE subscription request"""
    cve_id: str = Field(..., description="CVE ID (e.g., CVE-2024-1234)")

    class Config:
        json_schema_extra = {
            "example": {
                "cve_id": "CVE-2024-1234"
            }
        }


class SubscriptionResponse(BaseModel):
    """Subscription response"""
    id: int
    user_id: int
    cve_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionDeleteResponse(BaseModel):
    """Subscription deletion response"""
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Unsubscribed successfully"
            }
        }


# ========== Error Schemas ==========

class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid credentials",
                "status_code": 401,
                "timestamp": "2024-03-19T12:00:00"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    detail: list[dict]
    status_code: int = 422
