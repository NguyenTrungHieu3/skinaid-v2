from pydantic import BaseModel
from typing import List

class ClassificationResult(BaseModel):
    severity: str
    severity_confidence: float

class EfficientNetResponse(BaseModel):
    success: bool = True
    classifier_name: str = "EfficientnetB0"
    classifications: List[ClassificationResult] = []
