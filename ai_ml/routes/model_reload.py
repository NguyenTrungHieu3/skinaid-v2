"""
Model Reload Router for AI/ML Service (PBI-27).

Internal API for hot-reloading models without restarting the service.
Used by the backend to switch model versions after activate/rollback.
"""

import logging
import threading
from pathlib import Path
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Header, Body
from pydantic import BaseModel

from configs.config import settings
from pipeline.analyzer import WoundAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["Internal - Model Reload"])


class ReloadRequest(BaseModel):
    """Request model for model reload."""
    model_type: str  # detection or classification
    model_path: str
    version_tag: str


class ReloadResponse(BaseModel):
    """Response model for model reload."""
    success: bool
    model_type: str
    previous_version: str
    new_version: str
    message: str


# Thread lock for safe reload operations
_reload_lock = threading.Lock()

# Global analyzer instance (will be initialized on first use)
_analyzer: Optional[WoundAnalyzer] = None
_analyzer_lock = threading.Lock()


def get_analyzer() -> WoundAnalyzer:
    """Get or create the global analyzer instance."""
    global _analyzer
    
    with _analyzer_lock:
        if _analyzer is None:
            logger.info("Initializing global WoundAnalyzer...")
            _analyzer = WoundAnalyzer(
                yolo_model_path=Path(settings.YOLO_MODEL_PATH),
                efficientnet_model_path=Path(settings.EFFICIENTNET_MODEL_PATH)
            )
            logger.info("WoundAnalyzer initialized successfully")
        
        return _analyzer


def reload_detector_model(model_path: str) -> bool:
    """
    Reload the detector model with a new file.
    
    Args:
        model_path: Path to new model file
        
    Returns:
        True if reload successful
    """
    try:
        analyzer = get_analyzer()
        
        # Reload detector model
        logger.info(f"Reloading detector model from: {model_path}")
        analyzer.detector.reload_model(model_path)
        logger.info("Detector model reloaded successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to reload detector model: {e}")
        return False


def reload_classifier_model(model_path: str) -> bool:
    """
    Reload the classifier model with a new file.
    
    Args:
        model_path: Path to new model file
        
    Returns:
        True if reload successful
    """
    try:
        analyzer = get_analyzer()
        
        # Reload classifier model
        logger.info(f"Reloading classifier model from: {model_path}")
        analyzer.classifier.reload_model(model_path)
        logger.info("Classifier model reloaded successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to reload classifier model: {e}")
        return False


@router.post("/reload-model", response_model=ReloadResponse)
async def reload_model(
    request: ReloadRequest,
    x_api_key: str = Header(None, alias="X-API-Key")
):
    """
    Reload a model at runtime.
    
    This is an internal API that requires the AI_API_KEY.
    It allows the backend to trigger a model reload after activation/rollback.
    
    **model_type**: Type of model to reload (detection or classification)
    **model_path**: Path to the new model file
    **version_tag**: Version tag being loaded
    """
    # Validate API key
    if not x_api_key or x_api_key != settings.AI_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    
    # Acquire reload lock to prevent concurrent reloads
    with _reload_lock:
        try:
            analyzer = get_analyzer()
            
            # Determine which model to reload
            if request.model_type.lower() == "detection":
                # Get current version before reload
                previous_version = analyzer.detector.get_current_version()
                
                # Reload model
                success = reload_detector_model(request.model_path)
                
                if success:
                    new_version = request.version_tag
                    message = f"Detection model reloaded: {previous_version} -> {new_version}"
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to reload detector model"
                    )
                    
            elif request.model_type.lower() == "classification":
                # Get current version before reload
                previous_version = analyzer.classifier.get_current_version()
                
                # Reload model
                success = reload_classifier_model(request.model_path)
                
                if success:
                    new_version = request.version_tag
                    message = f"Classification model reloaded: {previous_version} -> {new_version}"
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to reload classifier model"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid model type: {request.model_type}. Must be 'detection' or 'classification'"
                )
            
            logger.info(f"Model reload completed: {message}")
            
            return ReloadResponse(
                success=True,
                model_type=request.model_type,
                previous_version=previous_version or "unknown",
                new_version=new_version,
                message=message
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Model reload failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Model reload failed: {str(e)}"
            )


@router.get("/model-status")
async def get_model_status(x_api_key: str = Header(None, alias="X-API-Key")):
    """
    Get current model status and versions.
    
    Requires API key authentication.
    """
    # Validate API key
    if not x_api_key or x_api_key != settings.AI_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    
    try:
        analyzer = get_analyzer()
        
        status = {
            "detection": {
                "version": analyzer.detector.get_current_version(),
                "model_path": str(analyzer.detector.model_path),
                "is_loaded": analyzer.detector.model is not None
            },
            "classification": {
                "version": analyzer.classifier.get_current_version(),
                "model_path": str(analyzer.classifier.model_path),
                "is_loaded": analyzer.classifier.model is not None
            }
        }
        
        return {"success": True, "status": status}
        
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model status: {str(e)}"
        )
