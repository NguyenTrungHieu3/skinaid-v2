from ultralytics import YOLO
from pathlib import Path
from typing import Optional
import sys
import cv2
import numpy as np
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from configs.config import settings

logger = logging.getLogger(__name__)

class WoundDetector:
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = Path(settings.YOLO_MODEL_PATH)
        else:
            model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"YOLO model not found: {model_path}")

        self.model_path = model_path
        self.model = YOLO(str(model_path))
        self.default_conf_threshold = settings.YOLO_CONF_THRESHOLD
        self._current_version: Optional[str] = None
    
    def get_current_version(self) -> Optional[str]:
        """Get the current model version tag."""
        return self._current_version
    
    def set_version(self, version_tag: str):
        """Set the current model version tag."""
        self._current_version = version_tag
    
    def reload_model(self, model_path: str) -> bool:
        """
        Reload the model from a new file path.
        
        Args:
            model_path: Path to the new model file
            
        Returns:
            True if reload successful
        """
        try:
            logger.info(f"Reloading YOLO model from: {model_path}")
            
            new_path = Path(model_path)
            if not new_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return False
            
            # Load new model
            self.model = YOLO(str(new_path))
            self.model_path = new_path
            
            logger.info(f"YOLO model reloaded successfully from: {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload YOLO model: {e}")
            return False

    def refine_bounding_box(self, image: np.ndarray, bbox: list) -> list:
        """
        Refine bounding box to tightly fit the wound area using color segmentation.
        Uses HSV color space to detect reddish/inflamed skin regions.
        
        Args:
            image: Full image in BGR format
            bbox: Original bounding box [x1, y1, x2, y2]
            
        Returns:
            Refined bounding box [x1, y1, x2, y2]
        """
        try:
            x1, y1, x2, y2 = map(int, bbox)
            
            # Crop to the detected region
            roi = image[y1:y2, x1:x2].copy()
            if roi.size == 0:
                return bbox
            
            # Convert to HSV
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Define range of red/inflamed skin colors
            # Lower bound for red/pinkish skin
            lower_red = np.array([0, 50, 50])
            upper_red = np.array([15, 255, 255])
            
            # Threshold the HSV image to get red components
            mask1 = cv2.inRange(hsv, lower_red, upper_red)
            
            # Red wraps around 180, so check upper end too
            lower_red2 = np.array([160, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            
            # Combine masks
            mask = cv2.bitwise_or(mask1, mask2)
            
            # Apply morphological operations to clean up noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Dilate to connect nearby regions
            mask = cv2.dilate(mask, kernel, iterations=2)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return bbox
            
            # Find the largest contour by area
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Check if contour is significant (at least 10% of ROI area)
            roi_area = roi.shape[0] * roi.shape[1]
            contour_area = cv2.contourArea(largest_contour)
            
            if contour_area < roi_area * 0.1:
                return bbox
            
            # Get bounding rect of the largest contour
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Add small padding (5 pixels) but ensure within bounds
            padding = 5
            new_x1 = max(0, x - padding)
            new_y1 = max(0, y - padding)
            new_x2 = min(roi.shape[1], x + w + padding)
            new_y2 = min(roi.shape[0], y + h + padding)
            
            # Convert back to original image coordinates
            refined_bbox = [
                x1 + new_x1,
                y1 + new_y1,
                x1 + new_x2,
                y1 + new_y2
            ]
            
            # Validate refined bbox has reasonable size
            new_w = new_x2 - new_x1
            new_h = new_y2 - new_y1
            
            if new_w < 20 or new_h < 20:
                return bbox
            
            return refined_bbox
            
        except Exception:
            # Return original bbox on any error
            return bbox

    def detect(self, image, conf_threshold: Optional[float] = None, refine_bbox: bool = True):
        try:
            if conf_threshold is None:
                conf_threshold = self.default_conf_threshold

            results = self.model.predict(source=image, conf=conf_threshold, save=False, verbose=False)
            detections = []

            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls)
                    conf = float(box.conf)
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    original_bbox = [x1, y1, x2, y2]
                    
                    # Refine bounding box if enabled
                    if refine_bbox:
                        refined_bbox = self.refine_bounding_box(image, original_bbox)
                        x1, y1, x2, y2 = refined_bbox
                    
                    detections.append({
                        "class_name": self.model.names[cls_id],
                        "confidence": round(conf, 2),
                        "bbox": [x1, y1, x2, y2],
                    })
            return detections
        except Exception:
            return []
