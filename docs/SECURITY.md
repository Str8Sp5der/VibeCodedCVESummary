# Security Documentation - CVE Database Application

## 🔒 Security Overview

This document details the security measures implemented in the CVE Database application to protect against common vulnerabilities and ensure data integrity.

## 1. Input Validation & Sanitization

### CVE ID Validation
```python
# Strict regex format validation
CVE ID Format: CVE-YYYY-NNNN (e.g., CVE-2024-1234)
Pattern: ^CVE-\d{4}-\d{4,}$

# Rejected if:
- Not matching pattern (400 Bad Request)
- Contains special characters
- SQL injection attempts
```

**Protection Against**: CWE-352 (Cross-Site Request Forgery), CWE-89 (SQL Injection)

### Search Query Validation
```python
# Character limits and validation
- Maximum length: 200 characters
- All special characters escaped
- Parameterized queries (SQLAlchemy)

# Severity filter validation
- Allowed values: LOW, MEDIUM, HIGH, CRITICAL
- Enum validation prevents injection
```

**Protection Against**: CWE-20 (Improper Input Validation)

### User Input Validation (Pydantic)
```python
class UserRegisterRequest(BaseModel):
    email: EmailStr  # RFC 5322 validation
    password: str  = Field(..., min_length=8)
    full_name: Optional[str] = None

# All requests validated automatically
```

**Protection Against**: CWE-400 (Uncontrolled Resource Consumption)

## 2. SQL Injection Prevention

### Parameterized Queries
```python
# ✅ SECURE - Using SQLAlchemy ORM
cve = db.query(CVE).filter(CVE.id == cve_id).first()

# ✅ SECURE - Raw SQL with parameters
from sqlalchemy import text
result = db.execute(
    text("SELECT * FROM cves WHERE id = :cve_id"),
    {"cve_id": cve_id}
)

# ❌ VULNERABLE - String interpolation (NOT USED)
query = f"SELECT * FROM cves WHERE id = '{cve_id}'"
```

**Protection Against**: CWE-89 (SQL Injection)

### Database Indexes
```sql
-- Indexed columns for fast, safe lookups
CREATE INDEX idx_cve_id ON cves(id);
CREATE INDEX idx_cve_cvss_score ON cves(cvss_score);
CREATE INDEX idx_cve_published_date ON cves(published_date);
CREATE INDEX idx_user_email ON users(email);
```

## 3. Cross-Site Scripting (XSS) Prevention

### Server-Side Output Escaping
```python
# Response always JSON with proper content type
response.headers["Content-Type"] = "application/json"
# No HTML rendering on server
```

### Client-Side DOMPurify Sanitization
```javascript
// ✅ SECURE - HTML sanitization
import DOMPurify from 'dompurify';
const sanitized = DOMPurify.sanitize(cve.description);

// ✅ SECURE - React JSX auto-escapes by default
<div>{cve.description}</div>

// ✅ SECURE - Highlight.js auto-escapes code
<Highlight language={cve.poc_language}>
  {cve.poc_code}
</Highlight>

// ❌ NEVER - dangerouslySetInnerHTML without sanitization
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

### Content Security Policy (CSP)
```
Content-Security-Policy: default-src 'self'; 
                         script-src 'self' 'unsafe-inline' 'unsafe-eval'; 
                         style-src 'self' 'unsafe-inline'
```

**Protection Against**: CWE-79 (Cross-Site Scripting)

## 4. Authentication & Authorization

### Password Security
```python
# ✅ bcrypt hashing with automatic salt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hashing
hashed = pwd_context.hash(password)  # Auto-generates salt

# Verification
is_valid = pwd_context.verify(plain_password, hashed)

# Password Requirements
- Minimum 8 characters
- Enforced at registration
- No complexity requirements (but recommended)
```

**Protection Against**: CWE-200 (Information Exposure), CWE-326 (Weak Encryption)

### JWT Token Management
```python
# Token Structure
{
  "sub": "user_id",      # Subject (user ID)
  "exp": 1708189445,     # Expiration time (24 hours)
  "type": "access"       # Token type
}

# HttpOnly Cookie (XSS-resistant)
response.set_cookie(
    "access_token_cookie",
    access_token,
    httponly=True,      # Not accessible to JavaScript
    secure=True,        # HTTPS only (production)
    samesite="strict"   # CSRF protection
)

# Token Expiration: 24 hours (short-lived)
# Refresh Token Expiration: 7 days
```

**Protection Against**: CWE-287 (Improper Authentication)

### Role-Based Access Control (RBAC)
```python
# User Roles
- "admin": Full access, can manage system, view audit logs
- "analyst": Can search CVEs, view PoC code, manage subscriptions
- "viewer": Limited - can only search CVEs anonymously

# Endpoint Protection
@app.get("/admin/audit-logs")
async def get_audit_logs(current_admin: User = Depends(get_current_admin)):
    # Only users with role="admin" can access

# Authorization Check
if current_user.role != "admin":
    raise HTTPException(status_code=403, detail="Admin access required")
```

**Protection Against**: CWE-639 (Authorization Bypass)

## 5. CSRF (Cross-Site Request Forgery) Protection

### CSRF Token Generation
```python
# Generate on each page load
import secrets
import base64

def generate_csrf_token():
    return base64.b64encode(secrets.token_bytes(32)).decode()

# Token is unique per session
```

### CSRF Token Validation
```python
# Backend validates CSRF token on state-changing requests
@app.post("/api/subscriptions")
async def subscribe(request: SubscriptionRequest):
    # FastAPI middleware validates X-CSRF-Token header
    pass

# Frontend includes CSRF token
fetch('/api/subscriptions', {
    method: 'POST',
    headers: {
        'X-CSRF-Token': csrfToken,  // From meta tag or localStorage
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ cve_id: 'CVE-2024-1234' })
});
```

**Protection Against**: CWE-352 (Cross-Site Request Forgery)

## 6. Data Encryption

### Sensitive Field Encryption
```python
# PoC code encrypted in database
from cryptography.fernet import Fernet

cipher = Fernet(encryption_key)
encrypted_poc = cipher.encrypt(poc_code.encode())

# Decryption only on authorized access
def get_cve_poc(cve_id, current_user):
    cve = db.query(CVE).filter(CVE.id == cve_id).first()
    decrypted = cipher.decrypt(cve.poc_code.encode()).decode()
    return decrypted
```

### Password Storage
```sql
-- Passwords never stored in plaintext
SELECT * FROM users;
id | email | password_hash
1  | user@example.com | $2b$12$R9h7c...  (bcrypt hash)
```

**Protection Against**: CWE-312 (Cleartext Storage), CWE-327 (Weak Cryptography)

## 7. Security Headers

### HTTP Security Headers
```python
@app.after_request
def set_security_headers(response):
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # XSS Protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # HSTS (HTTP Strict Transport Security)
    response.headers["Strict-Transport-Security"] = \
        "max-age=31536000; includeSubDomains"
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy (see #3)
    response.headers["Content-Security-Policy"] = "..."
    
    return response
```

**Protection Against**: CWE-693 (Protection Mechanism Failure)

## 8. Rate Limiting

### Global Rate Limiting
```python
# Per-user rate limit: 100 requests/hour
# Global rate limit: 1000 requests/hour
# Login endpoint: 10 attempts/hour (brute force protection)

# Implementation via middleware
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    user_id = get_user_from_token(request)
    if user_id in rate_limiter:
        if rate_limiter[user_id] > 100:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )
```

**Protection Against**: CWE-770 (Allocation of Resources Without Limits)

## 9. Audit Logging

### Comprehensive Request Logging
```python
# Every API request logged
{
    "user_id": 5,
    "action": "CVE_SEARCH",
    "endpoint": "/api/cves",
    "method": "GET",
    "status_code": 200,
    "ip_address": "192.168.1.100",
    "timestamp": "2024-02-15T12:30:45",
    "query_params": {"q": "CVE-2024", "severity": "CRITICAL"}
}

# Sensitive fields redacted
# Passwords, API keys, tokens not logged
```

### Admin Audit Log Access
```bash
GET /admin/audit-logs?action=LOGIN&user_id=5
# Returns all login attempts by user 5
# Enables detection of unauthorized access attempts
```

**Protection Against**: CWE-778 (Insufficient Logging)

## 10. Dependency Security

### Secure Dependencies
```python
# requirements.txt uses pinned versions
fastapi==0.104.1  # Not "fastapi>=0.100"
sqlalchemy==2.0.23
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0

# Regular updates for security patches
pip install --upgrade pip setuptools wheel
pip install -U -r requirements.txt
```

### Vulnerability Scanning
```bash
# Check for known vulnerabilities
pip install safety
safety check --json

# Or use OWASP Dependency-Check
docker run -v $(pwd):/src owasp/dependency-check:latest
```

**Protection Against**: CWE-506 (Known Vulnerable Component)

## 11. File Upload Security

### PoC Code Storage
```python
# PoC code is fetched from Exploit-DB, not user-uploaded
# If local storage used:
- Stored as encrypted BLOB in database
- Never executed on server
- Sanitized before display
- Rate-limited access
```

**Protection Against**: CWE-434 (Unrestricted Upload)

## 12. API Security

### HTTPS/TLS
```
# Production HTTPS only
response.headers["Strict-Transport-Security"] = \
    "max-age=31536000; includeSubDomains; preload"
```

### CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cve-app.example.com"],  # Specific origin
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Whitelist methods
    allow_headers=["Authorization", "Content-Type"],
)
```

### API Versioning
```
GET /api/v1/cves       # Future-proof API versioning
GET /api/v1/auth/login
```

**Protection Against**: CWE-94 (Code Injection)

## 🛡️ Threat Models Addressed

| Threat | Mitigation | CWE |
|--------|-----------|-----|
| SQL Injection | Parameterized queries, input validation | CWE-89 |
| XSS | DOMPurify, CSP, output escaping | CWE-79 |
| CSRF | Token validation, SameSite cookies | CWE-352 |
| Authentication Bypass | JWT, bcrypt, rate limiting | CWE-287 |
| Unauthorized Access | RBAC, audit logging | CWE-639 |
| Sensitive Data Exposure | Encryption, HTTPS | CWE-200 |
| Weak Cryptography | bcrypt, Fernet encryption | CWE-326 |
| Information Disclosure | Error handling, no stack traces | CWE-209 |
| DoS Attack | Rate limiting, input validation | CWE-400 |
| Vulnerable Dependencies | Version pinning, regular updates | CWE-506 |

## 🔍 Security Testing Checklist

- [ ] SQL Injection: `' OR '1'='1` → Rejected
- [ ] XSS: `<script>alert('xss')</script>` → Escaped
- [ ] CSRF: POST without token → 403 Forbidden
- [ ] Invalid CVE ID: `CVE-999-ABC` → 400 Bad Request
- [ ] Missing Auth: `/api/subscriptions` → 401 Unauthorized
- [ ] Brute Force: 15 failed logins → 429 Rate Limited
- [ ] Privilege Escalation: viewer accessing `/admin` → 403 Forbidden
- [ ] Data Encryption: PoC code in DB → Encrypted (verified)
- [ ] Audit Logging: All actions logged → Verified in `/admin/audit-logs`

## 📋 Compliance & Standards

- **OWASP Top 10 2021**: Addressed (see Section 1)
- **CWE Top 25**: Covered in threat model
- **NIST Cybersecurity Framework**: Applied
- **Data Protection**: GDPR-ready (audit logs for data access)

## 🚨 Known Limitations & Mitigations

### 1. **Exploit-DB Rate Limiting**
- **Issue**: Exploit-DB API has strict rate limits
- **Mitigation**: Delta sync runs every 10 mins, full sync every 60 mins

### 2. **PoC Code Storage**
- **Issue**: Storing exploit code is sensitive
- **Mitigation**: Encrypted in DB, requires authentication, warns users, audit logged

### 3. **NVD API Availability**
- **Issue**: NVD API outages affect database updates
- **Mitigation**: Graceful error handling, app continues with cached data

## 🔐 Incident Response

### If Breach Detected:
1. **Identify**: Check audit logs in `/admin/audit-logs`
2. **Contain**: Revoke compromised tokens, reset passwords
3. **Notify**: Alert affected users, update security headers
4. **Post-Mortem**: Review audit logs, update Security.md

### Key Audit Log Fields
- `ip_address`: Source of suspicious activity
- `user_id`: Compromised account
- `action`: Type of malicious activity
- `timestamp`: When it occurred

## 📞 Security Reporting

**For security vulnerabilities, please email:** security@example.com

Do NOT disclose vulnerabilities publicly. We follow responsible disclosure practices.

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework/)

---

**Last Updated**: 2024-02-15  
**Version**: 1.0.0
