import torch
import timm
import cv2
from torchvision import transforms
from PIL import Image

class SeverityClassifier:
    def __init__(self, model_path: str, num_classes=7):
        self.model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=num_classes)
        state_dict = torch.load(model_path, map_location='cpu')
        self.model.load_state_dict(state_dict)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        self.classes = [
            "abrasion mild", "abrasion moderate",
            "bruise mild", "bruise moderate",
            "burn mild", "burn moderate blister", "burn moderate skintear"
        ]

    def classify(self, cropped_image):
        img = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        input_tensor = self.transform(img).unsqueeze(0)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probs = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, dim=1)

        return self.classes[predicted.item()], round(confidence.item(), 2)
