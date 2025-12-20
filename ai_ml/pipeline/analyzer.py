import sys
from pathlib import Path
from typing import Optional

ai_ml_root = Path(__file__).parent.parent
sys.path.insert(0, str(ai_ml_root))

from models.detection.wound_detector import WoundDetector
from models.classification.wound_classifier import SeverityClassifier
from configs.config import settings


class WoundAnalyzer:
    def __init__(
        self,
        yolo_model_path: Optional[str] = None,
        efficientnet_model_path: Optional[str] = None,
    ):
        if yolo_model_path is None:
            yolo_model_path = Path(settings.YOLO_MODEL_PATH)
        else:
            yolo_model_path = Path(yolo_model_path)

        if efficientnet_model_path is None:
            efficientnet_model_path = Path(settings.EFFICIENTNET_MODEL_PATH)
        else:
            efficientnet_model_path = Path(efficientnet_model_path)

        self.detector = WoundDetector(str(yolo_model_path))
        self.classifier = SeverityClassifier(str(efficientnet_model_path))

    def crop_boxes(self, image, boxes):
        crops = []
        try:
            h, w, _ = image.shape
            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 > x1 and y2 > y1:
                    crops.append(image[y1:y2, x1:x2])
            return crops
        except Exception:
            return []

    def getConfidenceFusion(
        self, yolo_conf: float, eff_conf: float, w_yolo: float, w_eff: float
    ) -> Optional[float]:
        return yolo_conf * w_yolo + eff_conf * w_eff

    def analyze(self, image, conf_threshold: Optional[float] = None):
        try:
            if conf_threshold is None:
                conf_threshold = settings.YOLO_CONF_THRESHOLD

            detections = self.detector.detect(image, conf_threshold)
            if not detections:
                return []

            boxes = [d["bbox"] for d in detections]
            crops = self.crop_boxes(image, boxes)

            results = []
            for i, crop in enumerate(crops):
                try:
                    severity, conf = self.classifier.classify(crop)

                    # Công thức kết hợp độ tin cậy
                    final_conf = self.getConfidenceFusion(
                        detections[i]["confidence"], conf, 0.3, 0.7
                    )
                    print("yolo_conf:", detections[i]["confidence"])
                    print("eff_conf:", conf)
                    print("final_conf:", final_conf)

                    results.append(
                        {
                            "bbox": detections[i]["bbox"],
                            "class_name": detections[i]["class_name"],
                            "wound_confidence": detections[i]["confidence"],
                            "severity": severity,
                            "severity_confidence": final_conf,
                        }
                    )
                except Exception:
                    continue
            return results
        except Exception:
            return []
