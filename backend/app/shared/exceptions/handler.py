import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from app.shared.exceptions.base import AppException

logger = logging.getLogger(__name__)


def _build_error_body(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "success": False,
        "error_code": error_code,
        "message": message,
        "details": details,
        "status_code": status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    logger.warning(
        "[%s] %s — %s | details=%s",
        request.method,
        request.url.path,
        exc.message,
        exc.details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_body(
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        ),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "[%s] %s — Unexpected error: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content=_build_error_body(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Đã xảy ra lỗi nội bộ, vui lòng thử lại",
            details={},
        ),
    )
