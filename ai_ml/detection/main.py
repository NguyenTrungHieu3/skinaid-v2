from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import uuid
from pathlib import Path
import logging

from .config import settings
from .model import detector
from .schemas import DetectionResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Detection Service...")
    logger.info(f"Model config: {settings.DETECTION_MODEL_PATH}")

    try:
        model_info = detector.get_model_info()
        logger.info(
            "Model loaded successfully",
            extra={
                "device": model_info.get("device"),
                "num_classes": model_info.get("num_classes"),
                "class_names": model_info.get("class_names")
            }
        )
    except Exception as e:
        logger.error(f"Failed to load model during startup: {e}")
        raise 
    
    yield 
    
    logger.info("Shutting down AI Detection Service...")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI Wound Detection Service using YOLOv11 - SkinAid Capstone 1",
    lifespan=lifespan 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "detect": "/detect",
            "model_info": "/model-info"
        }
    }

@app.get("/health")
async def health_check():
    try:
        model_info = detector.get_model_info()
        
        return {
            "status": "healthy" if model_info.get("loaded") else "unhealthy",
            "service": settings.APP_NAME,
            "model_loaded": model_info.get("loaded", False),
            "device": model_info.get("device", "unknown")
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": settings.APP_NAME,
            "error": str(e)
        }

@app.get("/model-info")
async def get_model_info():
    try:
        return detector.get_model_info()
    except Exception as e:
        logger.error(f"Model info retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve model info: {str(e)}"
        )

@app.post("/detect", response_model=DetectionResponse)
async def detect_wound(file: UploadFile = File(...)):
    start_time = time.time()
    temp_file_path = None
    
    try:
        allowed_types = ["image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. "
                       f"Only JPEG/PNG allowed. Your file: {file.filename}"
            )
        
        file_extension = Path(file.filename).suffix if file.filename else ".jpg"
        temp_filename = f"{uuid.uuid4().hex}{file_extension}"
        temp_file_path = settings.TEMP_UPLOAD_DIR / temp_filename
        
        logger.info(f"Saving uploaded file to: {temp_file_path}")
        
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Running inference on: {temp_file_path}")
        
        result = await detector.predict_async(str(temp_file_path))
        
        if not result.get("success"):
            error_msg = result.get("error", "Inference failed")
            logger.error(f"AI inference failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"AI inference failed: {error_msg}"
            )
        
        processing_time = time.time() - start_time
        
        response = DetectionResponse(
            success=True,
            num_detections=result["num_detections"],
            detections=result["detections"],
            image_size=result["image_size"],
            processing_time=round(processing_time, 3),
            ai_model_version="YOLOv11_v1.0"
        )
        
        logger.info(
            f"Detection completed: {result['num_detections']} wounds found "
            f"in {processing_time:.3f}s"
        )
        
        return response
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"Detection endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
    finally:
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.info(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )