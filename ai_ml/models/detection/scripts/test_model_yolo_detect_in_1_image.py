from ultralytics import YOLO
import cv2

model = YOLO(r"..\models\best_v2.pt")
img_path = r"D:\NCKH\C1SE.24_SkinAid_Capstone1\ai_ml\data\raw_dataset\yolo_dataset\yolo_dataset_1_class_wound\test\images\istockphoto-1473174152-612x612_jpg.rf.36d17646cadbbab6b0a250aa7a71f5f1.jpg"
results = model.predict(source=img_path, conf = 0.25, save = False)

for result in results: 
    img = result.plot()
    cv2.imshow("Test Yolo Detection", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

for box in results[0].boxes:
    cls_id = int(box.cls)
    confidence = float(box.conf)
    print(f"Class {model.names[cls_id]}, Confidence {float(confidence):.2f}")
