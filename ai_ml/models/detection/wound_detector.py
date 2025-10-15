from ultralytics import YOLO

class WoundDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)

    def detect(self, image, conf_threshold=0.25):
        results = self.model.predict(source=image, conf=conf_threshold, save=False)
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
