"""
Admin Audit Middleware

This middleware automatically logs admin actions to the audit trail.
It intercepts requests to admin endpoints and creates audit log entries.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Callable, Optional
import time
import logging
import json

from app.core.database import get_db_session
from app.modules.admin.services.audit_service import AdminAuditService

logger = logging.getLogger(__name__)


class AdminAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log admin actions.
    
    This middleware:
    - Intercepts requests to /api/v1/admin/* endpoints
    - Logs CREATE, UPDATE, DELETE operations
    - Captures request details (method, path, IP, user agent)
    - Records operation timing
    - Creates audit trail entries
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Actions that should be audited
        self.auditable_methods = {"POST", "PUT", "PATCH", "DELETE"}
        
        # Mapping of HTTP methods to action prefixes
        self.method_to_action = {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE"
        }
        
        # Mapping of resource paths to resource types
        self.resource_patterns = {
            "/api/v1/admin/users": "user",
            "/api/v1/first-aid/guides": "first_aid_guide",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and create audit log if applicable"""
        
        # Check if this is an admin endpoint that should be audited
        path = request.url.path
        method = request.method
        
        should_audit = (
            method in self.auditable_methods and
            any(path.startswith(pattern) for pattern in self.resource_patterns)
        )
        
        if not should_audit:
            # Not an auditable request, just pass through
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        status = "success"
        error_message = None
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Check if request failed
            if response.status_code >= 400:
                status = "failed"
                if response.status_code >= 500:
                    error_message = f"Server error: {response.status_code}"
                else:
                    error_message = f"Client error: {response.status_code}"
            
        except Exception as e:
            status = "failed"
            error_message = str(e)
            raise
        
        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Create audit log entry (asynchronously, don't block response)
            try:
                await self._create_audit_log(
                    request=request,
                    status=status,
                    error_message=error_message,
                    duration_ms=duration_ms
                )
            except Exception as e:
                # Log error but don't fail the request
                logger.error(f"Failed to create audit log: {e}", exc_info=True)
        
        return response
    
    async def _create_audit_log(
        self,
        request: Request,
        status: str,
        error_message: Optional[str],
        duration_ms: int
    ):
        """Create an audit log entry for the request"""
        
        # Extract admin user info from request state (set by auth middleware)
        current_user = getattr(request.state, "current_user", None)
        
        if not current_user:
            logger.warning(f"No current_user in request state for {request.url.path}")
            return
        
        # Determine action and resource type
        method = request.method
        path = request.url.path
        
        action_prefix = self.method_to_action.get(method, "UNKNOWN")
        resource_type = self._get_resource_type(path)
        action = f"{action_prefix}_{resource_type.upper()}"
        
        # Extract resource ID from path if present
        resource_id = self._extract_resource_id(path)
        
        # Get client info
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Create description
        description = f"{current_user.email} performed {action} on {resource_type}"
        if resource_id:
            description += f" (ID: {resource_id})"
        
        # Get database session
        async for db in get_db_session():
            try:
                audit_service = AdminAuditService(db)
                
                await audit_service.log_action(
                    admin_user_id=current_user.user_id,
                    admin_email=current_user.email,
                    admin_role=current_user.role,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    description=description,
                    metadata={
                        "request_id": request.headers.get("x-request-id"),
                        "query_params": dict(request.query_params),
                    },
                    http_method=method,
                    endpoint=path,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status=status,
                    error_message=error_message,
                    duration_ms=duration_ms
                )
            finally:
                await db.close()
    
    def _get_resource_type(self, path: str) -> str:
        """Extract resource type from request path"""
        for pattern, resource_type in self.resource_patterns.items():
            if path.startswith(pattern):
                return resource_type
        return "unknown"
    
    def _extract_resource_id(self, path: str) -> Optional[str]:
        """
        Extract resource ID from path.
        
        Assumes pattern: /api/v1/resource/{id}
        """
        parts = path.split("/")
        
        # Look for UUID-like segments (basic check)
        for part in reversed(parts):
            if len(part) == 36 and "-" in part:  # Basic UUID format check
                return part
        
        return None
