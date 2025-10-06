from ultralytics import YOLO
import torch
from pathlib import Path
import logging
import asyncio
from threading import Lock
from typing import Dict, Any, Optional
from .config import settings

logger = logging.getLogger(__name__)

class WoundDetectionModel: 
    _instance: Optional['WoundDetectionModel'] = None
    _model: Optional[YOLO] = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None: 
            with cls._lock: 
                if cls._instance is None: 
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self): 
        if not hasattr(self, '_initialized'):
            self._initialized = True
            if self._model is None: 
                self._load_model()
    
    def _load_model(self) -> None: 
        try: 
            model_path = settings.DETECTION_MODEL_PATH
            if not model_path.exists(): 
                raise FileNotFoundError(
                    f"Model file not found: {model_path}\n"
                    f"Please ensure the model file is in the correct location."
                )
            logger.info(f"Loading YOLO model from {model_path}")

            self._model = YOLO(str(model_path))

            device = 'cuda' if (
                settings.MODEL_DEVICE == 'cuda' and torch.cuda.is_available()
            ) else 'cpu'

            self._model.to(device)

            logger.info(
                f"Model loaded successfully",
                extra={
                    "device": device,
                    "model_path": str(model_path),
                    "model_size_mb": model_path.stat().st_size / (1024 * 1024),
                    "cuda_available": torch.cuda.is_available()
                }
            )
        except FileNotFoundError:
            logger.error(f"Model file not found: {model_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise RuntimeError(f"Model loading failed: {e}") from e
        
    async def predict_async(self, image_path: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self.predict_sync, image_path)
    
    def predict_sync(self, image_path: str) -> Dict[str, Any]:
        try:
            if not Path(image_path).exists():
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}",
                    "num_detections": 0,
                    "detections": []
                }

            with torch.inference_mode():
                results = self._model.predict(
                    source=image_path,
                    conf=settings.DETECTION_CONFIDENCE_THRESHOLD,
                    iou=settings.DETECTION_IOU_THRESHOLD,
                    imgsz=settings.IMAGE_SIZE,
                    max_det=settings.DETECTION_MAX_DETECTIONS,
                    verbose=False
                )

            if not results or len(results) == 0:
                logger.warning(f"No results returned from YOLO for {image_path}")
                return {
                    "success": True,
                    "num_detections": 0,
                    "detections": [],
                    "image_size": {"width": 0, "height": 0}
                }
            
            result = results[0]

            img_height, img_width = result.orig_shape 
            image_area = img_width * img_height

            detections = []
            boxes = result.boxes
            
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    xyxy = box.xyxy.cpu().numpy()[0] 
                    confidence = float(box.conf.cpu().numpy()[0])
                    class_id = int(box.cls.cpu().numpy()[0])

                    class_name = self._model.names.get(class_id, "unknown")

                    x1, y1, x2, y2 = xyxy
                    width = x2 - x1
                    height = y2 - y1
                    area = width * height

                    severity = self._determine_severity(area, image_area)
                    
                    detections.append({
                        "class_name": class_name,
                        "confidence": round(confidence, 3),
                        "bbox": {
                            "x": int(x1),
                            "y": int(y1),
                            "width": int(width),
                            "height": int(height)
                        },
                        "severity": severity
                    })
            
            return {
                "success": True,
                "num_detections": len(detections),
                "detections": detections,
                "image_size": {
                    "width": img_width,
                    "height": img_height
                }
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Prediction failed: {str(e)}",
                "num_detections": 0,
                "detections": []
            }
    
    def _determine_severity(self, wound_area: float, image_area: float) -> str:
        if image_area == 0:
            return "mild" 
        
        ratio = wound_area / image_area
        
        if ratio < 0.01:
            return "mild"
        elif ratio < 0.05: 
            return "moderate"
        else:
            return "severe"
    
    def get_model_info(self) -> Dict[str, Any]:
        if self._model is None:
            return {"loaded": False}
        
        try:
            device = next(self._model.model.parameters()).device
        except Exception:
            device = "unknown"
        
        return {
            "loaded": True,
            "device": str(device),
            "model_path": str(settings.DETECTION_MODEL_PATH),
            "num_classes": len(self._model.names) if self._model.names else 0,
            "class_names": list(self._model.names.values()) if self._model.names else [],
            "confidence_threshold": settings.DETECTION_CONFIDENCE_THRESHOLD
        }

detector = WoundDetectionModel()