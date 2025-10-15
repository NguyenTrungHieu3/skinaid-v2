from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FirstAidInstruction(BaseModel):
    do: List[str] = Field(..., description="List of things to do")
    dont: List[str] = Field(..., description="List of things not to do")

class FirstAidInformation(BaseModel):
    cause: Optional[str] = Field(None, description="Cause of the wound")
    symptoms: Optional[str] = Field(None, description="Symptoms of the wound")
    risks: Optional[str] = Field(None, description="Risks associated with the wound")

class FirstAidGuideResponse(BaseModel):
    firstaidguides_id: str = Field(..., description="First aid guide ID")
    wound_type: str = Field(..., description="Type of wound")
    severity: str = Field(..., description="Severity level")
    information: FirstAidInformation = Field(..., description="Information about the wound")
    instructions: FirstAidInstruction = Field(..., description="First aid instructions")
    tip: Optional[str] = Field(None, description="Easy to remember tip")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

class WoundTypeResponse(BaseModel):
    wound_type: str = Field(..., description="Type of wound")
    severities: List[str] = Field(..., description="Available severity levels")

class FirstAidSearchResponse(BaseModel):
    results: List[FirstAidGuideResponse] = Field(..., description="List of first aid guides")