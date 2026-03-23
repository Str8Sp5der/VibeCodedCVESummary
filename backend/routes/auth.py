import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse,
    AuthResponse, UserResponse, TokenRefreshRequest, CSRFTokenResponse
)
from security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, generate_csrf_token
)
from config import get_settings
from dependencies import get_current_user

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    csrf_token: str = Header(None, alias="X-CSRF-Token"),  # FIX: Add CSRF validation
    db: Session = Depends(get_db)
):
    """
    Register a new user
    Requires CSRF token for security
    """
    # FIX: Validate CSRF token is provided
    if not csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token required",
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Validate password strength (simple check)
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
    
    # Create new user
    new_user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role="viewer",  # Default role
        is_active=True,
        is_verified=False,  # In production, send verification email
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"User registered: {new_user.email}")
    
    # Create tokens
    access_token = create_access_token({"sub": str(new_user.id)})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})
    
    return {
        "user": UserResponse.from_orm(new_user),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/login", response_model=AuthResponse)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login user with email and password
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"User logged in: {user.email}")
    
    # Create tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "user": UserResponse.from_orm(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    payload = decode_token(request.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Create new access token
    access_token = create_access_token({"sub": str(user.id)})
    
    logger.info(f"Token refreshed for user: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": request.refresh_token,
        "expires_in": settings.JWT_EXPIRATION_HOURS * 3600,
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (token becomes invalid on client-side)
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information
    """
    return UserResponse.from_orm(current_user)
