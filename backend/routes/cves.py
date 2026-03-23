import logging
import math
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models.cve import CVE
from models.subscription import Subscription
from schemas import (
    CVESearchResponse, CVEResponse, CVEDetailResponse,
    SubscriptionRequest, SubscriptionResponse, CSRFTokenResponse,
    SubscriptionDeleteResponse  # Add this import
)
from dependencies import get_current_user, optional_current_user
from models.user import User
from security import generate_csrf_token, validate_cve_id, decrypt_data  # Add decrypt_data import
from services.nvd_sync import NVDSyncService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["CVE"])


@router.get("/cves", response_model=CVESearchResponse)
async def search_cves(
    q: str = Query(None, min_length=1, max_length=200, description="Search query"),
    severity: str = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    year: int = Query(None, ge=1999, le=2100, description="Filter by publication year"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
):
    """
    Search CVEs with optional filtering
    
    - **q**: Search term in CVE description or ID
    - **severity**: Filter by CVSS severity (LOW, MEDIUM, HIGH, CRITICAL)
    - **year**: Filter by publication year
    - **page**: Pagination (1-indexed)
    - **limit**: Results per page (max 100)
    """
    
    # Build query
    query = db.query(CVE)
    
    # Text search
    if q:
        search_pattern = f"%{q}%"
        query = query.filter(
            (CVE.id.ilike(search_pattern)) | (CVE.description.ilike(search_pattern))
        )
    
    # Severity filter (based on CVSS score)
    if severity:
        severity_upper = severity.upper()
        if severity_upper == "CRITICAL":
            query = query.filter(CVE.cvss_score >= 9.0)
        elif severity_upper == "HIGH":
            query = query.filter((CVE.cvss_score >= 7.0) & (CVE.cvss_score < 9.0))
        elif severity_upper == "MEDIUM":
            query = query.filter((CVE.cvss_score >= 4.0) & (CVE.cvss_score < 7.0))
        elif severity_upper == "LOW":
            query = query.filter((CVE.cvss_score >= 0.1) & (CVE.cvss_score < 4.0))
    
    # Year filter
    if year:
        query = query.filter(CVE.id.like(f"CVE-{year}-%"))
    
    # Get total count before pagination
    total = query.count()
    
    # Pagination
    skip = (page - 1) * limit
    items = query.order_by(desc(CVE.published_date)).offset(skip).limit(limit).all()
    
    # Convert to response format
    cve_responses = [CVEResponse.from_orm(cve) for cve in items]
    
    return CVESearchResponse(
        total=total,
        items=cve_responses,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit) if total > 0 else 1,
    )


@router.get("/cves/{cve_id}", response_model=CVEDetailResponse)
async def get_cve_detail(
    cve_id: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific CVE
    
    - **cve_id**: CVE ID (e.g., CVE-2024-1234)
    """
    
    # Validate CVE ID format
    if not validate_cve_id(cve_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CVE ID format. Expected format: CVE-YYYY-NNNN",
        )
    
    # Query database
    cve = db.query(CVE).filter(CVE.id == cve_id).first()
    
    if not cve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CVE {cve_id} not found",
        )
    
    return CVEDetailResponse.from_orm(cve)


@router.get("/cves/{cve_id}/poc")
async def get_cve_poc(
    cve_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get PoC (Proof of Concept) code for a CVE
    Requires authentication for audit logging
    
    - **cve_id**: CVE ID (e.g., CVE-2024-1234)
    """
    
    # Validate CVE ID format
    if not validate_cve_id(cve_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CVE ID format",
        )
    
    # Query database
    cve = db.query(CVE).filter(CVE.id == cve_id).first()
    
    if not cve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CVE {cve_id} not found",
        )
    
    if not cve.has_poc or not cve.poc_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No PoC available for {cve_id}",
        )
    
    # FIX: Decrypt PoC code if encrypted
    poc_code = cve.poc_code
    try:
        poc_code = decrypt_data(cve.poc_code)
    except Exception as e:
        logger.error(f"Failed to decrypt PoC for {cve_id}: {e}")
        # If decryption fails, try using as-is (may be old unencrypted data)
        poc_code = cve.poc_code
    
    return {
        "cve_id": cve_id,
        "poc_code": poc_code,
        "poc_language": cve.poc_language,
        "poc_source": cve.poc_source,
        "warning": "This is exploit code. Use only in authorized environments.",
    }


@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_to_cve(
    request: SubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Subscribe to CVE alerts for a specific CVE
    
    - **cve_id**: CVE ID (e.g., CVE-2024-1234)
    """
    
    # Validate CVE ID
    if not validate_cve_id(request.cve_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CVE ID format",
        )
    
    # Check if CVE exists
    cve = db.query(CVE).filter(CVE.id == request.cve_id).first()
    if not cve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CVE {request.cve_id} not found",
        )
    
    # Check if already subscribed
    existing = db.query(Subscription).filter(
        (Subscription.user_id == current_user.id) &
        (Subscription.cve_id == request.cve_id)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already subscribed to {request.cve_id}",
        )
    
    # Create subscription
    subscription = Subscription(
        user_id=current_user.id,
        cve_id=request.cve_id,
    )
    
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    
    logger.info(f"User {current_user.email} subscribed to {request.cve_id}")
    
    return SubscriptionResponse.from_orm(subscription)


@router.delete("/subscriptions/{cve_id}", response_model=SubscriptionDeleteResponse)  # FIX: Add response_model
async def unsubscribe_from_cve(
    cve_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Unsubscribe from CVE alerts
    
    - **cve_id**: CVE ID (e.g., CVE-2024-1234)
    """
    
    # Validate CVE ID
    if not validate_cve_id(cve_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CVE ID format",
        )
    
    # Find and delete subscription
    subscription = db.query(Subscription).filter(
        (Subscription.user_id == current_user.id) &
        (Subscription.cve_id == cve_id)
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription for {cve_id} not found",
        )
    
    db.delete(subscription)
    db.commit()
    
    logger.info(f"User {current_user.email} unsubscribed from {cve_id}")
    
    return {"message": "Unsubscribed successfully"}


@router.get("/subscriptions")
async def get_user_subscriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's CVE subscriptions with pagination
    """
    
    # Query subscriptions
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    )
    
    total = subscriptions.count()
    skip = (page - 1) * limit
    
    items = subscriptions.order_by(desc(Subscription.created_at)).offset(skip).limit(limit).all()
    
    # Get full CVE data for subscriptions
    cves = []
    for sub in items:
        cve = db.query(CVE).filter(CVE.id == sub.cve_id).first()
        if cve:
            cves.append(CVEResponse.from_orm(cve))
    
    return {
        "total": total,
        "items": cves,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit) if total > 0 else 1,
    }
