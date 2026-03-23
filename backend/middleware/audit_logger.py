import logging
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal

logger = logging.getLogger(__name__)


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for audit tracking"""
    
    # Endpoints to skip audit logging
    SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
    
    async def dispatch(self, request: Request, call_next):
        # Check if path should be skipped
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Extract request info
        method = request.method
        path = request.url.path
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Get user from token if available
        user_id = None
        try:
            from security import decode_token
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = decode_token(token)
                if payload:
                    user_id = payload.get("sub")
        except Exception as e:
            logger.debug(f"Could not extract user from token: {e}")
        
        # Get request body (sanitized)
        request_body = {}
        try:
            if method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    import json
                    request_body = json.loads(body)
                    # Remove sensitive fields
                    for key in ["password", "token", "api_key", "secret"]:
                        request_body.pop(key, None)
        except Exception as e:
            logger.debug(f"Could not parse request body: {e}")
        
        # Call the actual endpoint
        start_time = datetime.utcnow()
        response = await call_next(request)
        end_time = datetime.utcnow()
        
        # Log the audit event
        try:
            db = SessionLocal()
            from models.audit_log import AuditLog
            
            action = f"{method} {path}"
            
            # Determine if successful
            response_status = "success" if 200 <= response.status_code < 300 else "error"
            
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource=path,
                method=method,
                endpoint=path,
                status_code=response.status_code,
                request_params=request_body,
                response_status=response_status,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=start_time,
            )
            db.add(audit_log)
            db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
        
        return response
