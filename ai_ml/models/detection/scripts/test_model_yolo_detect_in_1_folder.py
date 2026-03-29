from ultralytics import YOLO

model = YOLO("../models/best_v2.pt")

results = model.predict(
    source=r"D:\NCKH\C1SE.24_SkinAid_Capstone1\ai_ml\data\raw_dataset\yolo_dataset\wound_dataset_1_class_1489_images\test\images",
    conf=0.25,
    save=True,
    project=r"D:\NCKH\C1SE.24_SkinAid_Capstone1\ai_ml\outputs\yolo_detection",
    name="wound_detection_results"
)

num_of_box = 0
sum_precision = 0
for i, result in enumerate(results): 
    print(f"Ảnh: {i+1} - Path: {result.path}")
    for box in result.boxes:
        cls_id = int(box.cls)
        confidence = float(box.conf)
        sum_precision+=confidence
        num_of_box+=1
        print(f"    -> Class: {model.names[cls_id]}, Confidence: {confidence:.2f}")

print(f"Average Confidence: {(sum_precision/num_of_box):.2f}")
