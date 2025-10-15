from pydantic import BaseModel
from typing import List

class ClassificationResult(BaseModel):
    severity: str
    severity_confidence: float

class EfficientNetResponse(BaseModel):
    classifications: List[ClassificationResult] = []
