import torch
import timm
from torchvision import transforms
from PIL import Image
import torch.nn.functional as F

num_classes = 7
model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=num_classes)

model_path = "../models/final_model_v2.pth"
checkpoint = torch.load(model_path, map_location='cpu')
# Support both raw state_dict and full checkpoint formats
state_dict = checkpoint.get("model_state", checkpoint)

model.load_state_dict(state_dict)
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

img_path = r"D:\NCKH\C1SE.24_SkinAid_Capstone1\ai_ml\data\processed_dataset\efficientnet_dataset\test\burn_moderate_skintear\train_merged_000061_jpg.rf.a955b1df5ff586c9aaa5ffc249bb3fd4_bbox0.jpg"
img = Image.open(img_path).convert('RGB')
input_tensor = transform(img).unsqueeze(0)

with torch.no_grad():
    outputs = model(input_tensor)
    probs = F.softmax(outputs, dim=1)
    confidence, predicted = torch.max(probs, 1)

classes = ["abrasion mild", "abrasion moderate", "bruise mild", "bruise moderate", "burn mild", "burn moderate blister", "burn moderate skintear"]
print(f"Predicted class: {classes[predicted.item()]}, Confidence: {confidence.item()}")