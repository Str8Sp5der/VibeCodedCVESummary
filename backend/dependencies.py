import logging
from datetime import datetime, timedelta
from typing import Optional, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from security import verify_password, decode_token, create_access_token, create_refresh_token
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

security = HTTPBearer()


async def get_current_user(
    credentials: Any = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify admin role
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return current_user


async def get_current_analyst(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify analyst or admin role
    """
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst access required",
        )
    
    return current_user


async def optional_current_user(
    request: Request,  # FIX: Changed from dict to Request
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    Useful for endpoints that work with or without auth
    """
    auth_header = request.headers.get("authorization", "")  # FIX: Use Request.headers instead of dict.get
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    return user if user and user.is_active else None
