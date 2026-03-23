import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


# JWT Token Management
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token with longer expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"Token decode error: {e}")
        return None


# Data Encryption (for sensitive fields like PoC code)
def get_encryption_key():
    """
    Get Fernet encryption key from settings.
    Converts the ENCRYPTION_KEY string to proper Fernet format.
    
    In production, this key should be:
    1. Generated with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    2. Stored securely in .env file
    3. Never committed to version control
    """
    import base64
    encryption_key = settings.ENCRYPTION_KEY
    
    # If key is already base64-encoded (starts from our generation), use as-is
    if encryption_key.startswith('gAAAAAB'):  # Common prefix for Fernet keys
        try:
            return encryption_key.encode()
        except Exception:
            pass
    
    # Otherwise, safely encode the string key to proper Fernet format
    # This ensures 32 bytes and proper base64 encoding
    key_bytes = encryption_key.encode().ljust(32, b'\0')[:32]
    safe_key = base64.urlsafe_b64encode(key_bytes)
    return safe_key


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data (e.g., PoC code)"""
    try:
        if not data:
            return data
        
        key = get_encryption_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(data.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        # Fallback: return data unencrypted (log this!)
        return data


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    try:
        if not encrypted_data:
            return encrypted_data
        
        key = get_encryption_key()
        cipher = Fernet(key)
        decrypted = cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        # Fallback: return as-is (may be unencrypted data from old entries)
        return encrypted_data


# CSRF Token Generation
import secrets
import base64


def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return base64.b64encode(secrets.token_bytes(32)).decode()


def validate_input_format(text: str, max_length: int = 1000) -> bool:
    """Basic input validation"""
    if not isinstance(text, str):
        return False
    if len(text) > max_length:
        return False
    return True


def validate_cve_id(cve_id: str) -> bool:
    """Validate CVE ID format: CVE-YYYY-NNNN"""
    import re
    pattern = r'^CVE-\d{4}-\d{4,}$'
    return bool(re.match(pattern, cve_id))


def sanitize_sql_input(value: str) -> str:
    """Basic SQL input sanitization (SQLAlchemy handles parameterized queries)"""
    # This is a safety net - parameterized queries are primary defense
    dangerous_chars = ["'", '"', ";", "--", "/*", "*/"]
    for char in dangerous_chars:
        value = value.replace(char, "")
    return value
