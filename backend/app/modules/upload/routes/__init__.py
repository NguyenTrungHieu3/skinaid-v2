# Upload Routes

from .upload_routers import router as upload_router
from .upload_validation_router import router as validation_router

__all__ = ["upload_router", "validation_router"]