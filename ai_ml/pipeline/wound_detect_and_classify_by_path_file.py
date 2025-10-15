from ultralytics import YOLO
import cv2
import torch
import timm
from torchvision import transforms
from PIL import Image

# Load model YOLO
model_yolo = YOLO("../detection/models/model_2_class_v1.pt")

# Load model efficientNet
num_classes = 7
model_efficientnet = timm.create_model("efficientnet_b0", pretrained=False, num_classes=num_classes)
efficientnet_model_path = "../classification/models/final_model.pth"
state_dict = torch.load(efficientnet_model_path, map_location='cpu')
model_efficientnet.load_state_dict(state_dict)
model_efficientnet.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])
 
# Detect function using yolo
def detect_wounds(img_path, conf_threshold=0.25):
    results = model_yolo.predict(source=img_path, conf=conf_threshold, save=False)
    detections = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls)
            conf = float(box.conf)
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            detections.append({
                "class_name": model_yolo.names[cls_id],
                "confidence": round(conf,2),
                "bbox": [x1, y1, x2, y2],
            })
    return detections

# Crop function by bounding box
def crop_wounds(img_path, boxes):
    image = cv2.imread(img_path)
    if (image is None):
        print(f"Không thể đọc ảnh: {img_path}")
        return []
    
    crops = []

    h, w, _ = image.shape
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        crop = image[y1:y2, x1:x2]
        crops.append(crop)

    return crops

# Classify serverity function
def classify_serverity(cropped_image, model=model_efficientnet, transform=transform):
    img = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    input_tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        outputs = model(input_tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probs, dim=1)

    classes = ["abrasion mild", "abrasion moderate", "bruise mild", "bruise moderate", "burn mild", "burn moderate blister", "burn moderate skintear"]
    return classes[predicted.item()], round(confidence.item(), 2)

def detect_and_clasify(img_path, conf_threshold=0.25):
    detected_wounds = detect_wounds(img_path, conf_threshold)
    boxes = []
    for detected_wound in detected_wounds:
        boxes.append(detected_wound["bbox"])
    cropped_images = crop_wounds(img_path, boxes)
    detected_and_classified_wounds = []
    for i, cropped_image in enumerate(cropped_images):
        severity, confidence = classify_serverity(cropped_image)
        detected_and_classified_wounds.append({
            "bbox": detected_wounds[i]["bbox"],
            "confidence": detected_wounds[i]["confidence"],
            "class_name": detected_wounds[i]["class_name"],
            "severity": severity,
            "severity_confidence": confidence
        })
    return detected_and_classified_wounds
