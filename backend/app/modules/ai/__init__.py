from .models.wound_analysis import WoundAnalysis
from .models.wound_detection import WoundDetection
from .controllers.ai_controller import AIController
from .routes.ai_router import router as ai_router

__all__ = [
    "WoundAnalysis",
    "WoundDetection",
    "AIController",
    "ai_router"
]