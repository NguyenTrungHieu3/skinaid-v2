import cv2
import sys
from pathlib import Path
from models.detection.wound_detector import WoundDetector
from models.classification.wound_classifier import SeverityClassifier

ai_ml_root = Path(__file__).parent.parent
sys.path.insert(0, str(ai_ml_root))

class WoundAnalyzer:
    def __init__(self, yolo_model_path, efficientnet_model_path):
        self.detector = WoundDetector(yolo_model_path)
        self.classifier = SeverityClassifier(efficientnet_model_path)

    def crop_boxes(self, image, boxes):
        crops = []
        h, w, _ = image.shape
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            crops.append(image[y1:y2, x1:x2])
        return crops

    def analyze(self, image, conf_threshold=0.25):
        detections = self.detector.detect(image, conf_threshold)
        boxes = [d["bbox"] for d in detections]
        crops = self.crop_boxes(image, boxes)

        results = []
        for i, crop in enumerate(crops):
            severity, conf = self.classifier.classify(crop)
            results.append({
                "bbox": detections[i]["bbox"],
                "class_name": detections[i]["class_name"],
                "wound_confidence": detections[i]["confidence"],
                "severity": severity,
                "severity_confidence": conf
            })
        return results
