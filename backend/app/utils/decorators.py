"""
⚠️  DEPRECATED — File này sẽ bị xóa khi refactor controllers.

Decorators xử lý lỗi — chỉ giữ lại tạm thời vì admin controller
vẫn đang sử dụng `handle_admin_errors`.
Khi refactor sang exception-based error handling, decorators này
sẽ không cần thiết nữa.

Xem: shared/exceptions/base.py cho hệ thống mới.
"""

import logging
import functools
from typing import Callable, Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def handle_admin_errors(operation_name: str):
    """
    Decorator xử lý lỗi cho admin controller methods.

    ⚠️ DEPRECATED: Sẽ bị xóa khi chuyển sang exception system mới.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)

            except HTTPException:
                raise

            except ValueError as e:
                error_msg = str(e)
                logger.warning(
                    f"[{operation_name}] Validation error: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

            except Exception as e:
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
    Decorator xử lý lỗi cho service layer.

    ⚠️ DEPRECATED: Sẽ bị xóa khi chuyển sang exception system mới.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)

            except ValueError:
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
    Decorator xử lý not-found cases.

    ⚠️ DEPRECATED: Sẽ bị xóa khi chuyển sang exception system mới.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            result = await func(*args, **kwargs)

            if result is None:
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
