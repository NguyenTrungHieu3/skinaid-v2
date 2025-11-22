"""
Reusable decorators for common functionality across the application.
"""

import logging
import functools
from typing import Callable, Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def handle_admin_errors(operation_name: str):
    """
    Decorator to handle errors in admin controller methods.
    
    This decorator provides consistent error handling and logging for admin operations,
    reducing boilerplate try/except blocks in controller methods.
    
    Args:
        operation_name: Name of the operation being performed (e.g., "delete_user", "update_user")
    
    Usage:
        @handle_admin_errors("delete_user")
        async def delete_user(self, user_id: UUID):
            # Your code here
            pass
    
    The decorator will:
    - Catch HTTPException and re-raise it (preserving custom error responses)
    - Catch ValueError and convert to 400 Bad Request
    - Catch all other exceptions and convert to 500 Internal Server Error
    - Log all errors appropriately
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            
            except HTTPException:
                # Re-raise HTTP exceptions as-is (they're already properly formatted)
                raise
            
            except ValueError as e:
                # Convert validation errors to 400 Bad Request
                error_msg = str(e)
                logger.warning(f"[{operation_name}] Validation error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            except Exception as e:
                # Catch-all for unexpected errors
                error_msg = str(e)
                logger.error(
                    f"[{operation_name}] Unexpected error: {error_msg}",
                    exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {operation_name.replace('_', ' ')}: {error_msg}"
                )
        
        return wrapper
    return decorator


def handle_service_errors(operation_name: str):
    """
    Decorator to handle errors in service layer methods.
    
    Similar to handle_admin_errors but for service layer.
    Logs errors but doesn't convert to HTTP exceptions (since services shouldn't know about HTTP).
    
    Args:
        operation_name: Name of the operation being performed
    
    Usage:
        @handle_service_errors("create_user")
        async def create_user(self, user_data):
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            
            except ValueError:
                # Re-raise validation errors as-is
                raise
            
            except Exception as e:
                logger.error(
                    f"[SERVICE:{operation_name}] Error: {str(e)}",
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def require_not_found_handling(resource_name: str, identifier_param: str = "id"):
    """
    Decorator to handle "not found" cases consistently.
    
    Expects the wrapped function to return None when resource is not found,
    and converts it to a 404 HTTPException.
    
    Args:
        resource_name: Name of the resource (e.g., "User", "Guide")
        identifier_param: Name of the parameter containing the resource ID
    
    Usage:
        @require_not_found_handling("User", "user_id")
        async def get_user_detail(self, user_id: UUID):
            user = await self.service.get_user(user_id)
            return user  # If None, will raise 404
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)
            
            if result is None:
                # Extract the identifier value from kwargs
                identifier_value = kwargs.get(identifier_param, "unknown")
                
                logger.warning(
                    f"{resource_name} not found: {identifier_param}={identifier_value}"
                )
                
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{resource_name} with {identifier_param} '{identifier_value}' not found"
                )
            
            return result
        
        return wrapper
    return decorator
