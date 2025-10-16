import torch
import timm
import cv2
from torchvision import transforms
from PIL import Image
import sys
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from configs.config import settings

class SeverityClassifier:
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = Path(settings.EFFICIENTNET_MODEL_PATH)
        else:
            model_path = Path(model_path)

        if not model_path.exists():
            raise FileNotFoundError(f"Efficientnet model not found: {model_path}")
        
        self.model_name = settings.EFFICIENTNET_MODEL_NAME
        self.num_classes = settings.EFFICIENTNET_NUM_CLASSES
        self.device = settings.EFFICIENTNET_DEVICE
        self.classes = settings.WOUND_CLASSES
        self.pretrained = settings.EFFICIENTNET_PRETRAINED

        self.model = timm.create_model(self.model_name, pretrained=self.pretrained, num_classes=self.num_classes)
        state_dict = torch.load(str(model_path), map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()

        img_size = settings.IMAGE_SIZE
        img_mean = settings.IMAGE_MEAN
        img_std = settings.IMAGE_STD

        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=img_mean,
                                 std=img_std)
        ])

    def classify(self, cropped_image):
        img = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        input_tensor = self.transform(img).unsqueeze(0)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probs = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, dim=1)

        severity_class = self.classes[predicted.item()]
        confidence_score = round(confidence.item(), 2)    
        return severity_class, confidence_score
