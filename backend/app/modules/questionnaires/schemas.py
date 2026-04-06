from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class AnswerOptionBase(BaseModel):
    answer_text: str
    triage_level: str
    icon_or_color: Optional[str] = None
    order_index: int = 0
    metadata_tags: Optional[Dict[str, Any]] = None

class AnswerOptionCreate(AnswerOptionBase):
    pass

class AnswerOptionUpdate(BaseModel):
    answer_text: Optional[str] = None
    triage_level: Optional[str] = None
    icon_or_color: Optional[str] = None
    order_index: Optional[int] = None
    metadata_tags: Optional[Dict[str, Any]] = None

class AnswerOptionResponse(AnswerOptionBase):
    answer_id: UUID
    question_id: UUID
    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    question_text: str
    order_index: int = 0
    is_multiple_choice: bool = False
    is_active: bool = True

class QuestionCreate(QuestionBase):
    answers: Optional[List[AnswerOptionCreate]] = None

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    order_index: Optional[int] = None
    is_multiple_choice: Optional[bool] = None
    is_active: Optional[bool] = None

class QuestionResponse(QuestionBase):
    question_id: UUID
    questionnaire_id: UUID
    answers: List[AnswerOptionResponse] = []
    model_config = ConfigDict(from_attributes=True)


class QuestionnaireBase(BaseModel):
    wound_type: str
    title: str
    description: Optional[str] = None
    is_active: bool = False

class QuestionnaireCreate(QuestionnaireBase):
    questions: Optional[List[QuestionCreate]] = None

class QuestionnaireUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class QuestionnaireResponse(QuestionnaireBase):
    questionnaire_id: UUID
    questions: List[QuestionResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
