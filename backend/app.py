import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import time

from config import get_settings
from database import init_db

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Remove server info
        response.headers.pop("Server", None)
        response.headers["Server"] = "CVE Database API/1.0"
        
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Add request timing tracking"""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
        )
        
        return response


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Secure CVE Database API for Cybersecurity Professionals",
    debug=settings.DEBUG,
)

# Add middleware (order matters)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Total-Count"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and background tasks on startup"""
    logger.info("Starting CVE Database API...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Initialize scheduler for background CVE sync
    try:
        from services.scheduler import init_scheduler
        init_scheduler()
        logger.info("Background scheduler initialized")
    except Exception as e:
        logger.warning(f"Scheduler initialization failed: {e}")
        # Don't raise - app can work without scheduler


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down CVE Database API...")
    
    try:
        from services.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception as e:
        logger.warning(f"Scheduler shutdown failed: {e}")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to CVE Database API",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Register routes
from routes.auth import router as auth_router
from routes.cves import router as cves_router
from routes.admin import router as admin_router

app.include_router(auth_router)
app.include_router(cves_router)
app.include_router(admin_router)

# Register middleware
from middleware.audit_logger import AuditLoggerMiddleware
app.add_middleware(AuditLoggerMiddleware)

logger.info("FastAPI app initialized with all routes and middleware")
