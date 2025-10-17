from ultralytics import YOLO
from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from configs.config import settings

class WoundDetector:
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = Path(settings.YOLO_MODEL_PATH)
        else:
            model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"YOLO model not found: {model_path}")

        self.model = YOLO(str(model_path))
        self.default_conf_threshold = settings.YOLO_CONF_THRESHOLD

    def detect(self, image, conf_threshold: Optional[float] = None):
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
                    detections.append({
                        "class_name": self.model.names[cls_id],
                        "confidence": round(conf, 2),
                        "bbox": [x1, y1, x2, y2],
                    })
            return detections
        except Exception:
            return []
