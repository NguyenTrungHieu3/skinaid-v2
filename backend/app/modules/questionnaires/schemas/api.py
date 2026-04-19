from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# Canonical wound types — must stay in sync with VALID_WOUND_TYPES in import_service
ALLOWED_WOUND_TYPES = {
    "burn", "abrasion", "bruise", "fungal", "acne", "psoriasis",
}

ALLOWED_TRIAGE_LEVELS = {"green", "yellow", "red"}


# ─── AnswerOption Schemas ─────────────────────────────────────────────────────

class AnswerOptionBase(BaseModel):
    answer_text: str = Field(..., min_length=1, max_length=500, description="Nội dung đáp án")
    triage_level: str = Field(..., description="Mức độ nghiêm trọng: green, yellow, red")
    icon_or_color: Optional[str] = None
    order_index: int = Field(default=0, ge=0, description="Thứ tự đáp án (>= 0)")
    metadata_tags: Optional[Dict[str, Any]] = None

    @field_validator("answer_text")
    @classmethod
    def validate_answer_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nội dung đáp án không được để trống")
        return v

    @field_validator("triage_level")
    @classmethod
    def validate_triage_level(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ALLOWED_TRIAGE_LEVELS:
            raise ValueError(
                f"Mức độ triage phải là một trong: {', '.join(sorted(ALLOWED_TRIAGE_LEVELS))}"
            )
        return v

class AnswerOptionCreate(AnswerOptionBase):
    pass

class AnswerOptionUpdate(BaseModel):
    answer_text: Optional[str] = Field(default=None, min_length=1, max_length=500)
    triage_level: Optional[str] = None
    icon_or_color: Optional[str] = None
    order_index: Optional[int] = Field(default=None, ge=0)
    metadata_tags: Optional[Dict[str, Any]] = None

    @field_validator("answer_text")
    @classmethod
    def validate_answer_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Nội dung đáp án không được để trống")
        return v

    @field_validator("triage_level")
    @classmethod
    def validate_triage_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().lower()
            if v not in ALLOWED_TRIAGE_LEVELS:
                raise ValueError(
                    f"Mức độ triage phải là một trong: {', '.join(sorted(ALLOWED_TRIAGE_LEVELS))}"
                )
        return v

class AnswerOptionResponse(AnswerOptionBase):
    answer_id: UUID
    question_id: UUID
    model_config = ConfigDict(from_attributes=True)


# ─── Question Schemas ─────────────────────────────────────────────────────────

class QuestionBase(BaseModel):
    question_text: str = Field(..., min_length=1, max_length=1000, description="Nội dung câu hỏi")
    order_index: int = Field(default=0, ge=0, description="Thứ tự câu hỏi (>= 0)")
    is_multiple_choice: bool = False
    is_active: bool = True

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nội dung câu hỏi không được để trống")
        return v

class QuestionCreate(QuestionBase):
    answers: Optional[List[AnswerOptionCreate]] = None

class QuestionUpdate(BaseModel):
    question_text: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    order_index: Optional[int] = Field(default=None, ge=0)
    is_multiple_choice: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Nội dung câu hỏi không được để trống")
        return v

class QuestionResponse(QuestionBase):
    question_id: UUID
    questionnaire_id: UUID
    answers: List[AnswerOptionResponse] = []
    model_config = ConfigDict(from_attributes=True)


# ─── Questionnaire Schemas ────────────────────────────────────────────────────

class QuestionnaireBase(BaseModel):
    wound_type: str = Field(..., description="Loại vết thương")
    title: str = Field(..., min_length=1, max_length=200, description="Tiêu đề bộ câu hỏi")
    description: Optional[str] = Field(default=None, max_length=1000)
    is_active: bool = False

    @field_validator("wound_type")
    @classmethod
    def validate_wound_type(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("Loại vết thương không được để trống")
        if v not in ALLOWED_WOUND_TYPES:
            raise ValueError(
                f"Loại vết thương phải là một trong: {', '.join(sorted(ALLOWED_WOUND_TYPES))}"
            )
        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tiêu đề không được để trống")
        return v

class QuestionnaireCreate(QuestionnaireBase):
    questions: Optional[List[QuestionCreate]] = None

class QuestionnaireUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_active: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Tiêu đề không được để trống")
        return v

class QuestionnaireResponse(BaseModel):
    questionnaire_id: UUID
    wound_type: str
    title: str
    description: Optional[str] = None
    is_active: bool = False
    questions: List[QuestionResponse] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Import Response Schemas ─────────────────────────────────────────────────

class ImportPreviewResponse(BaseModel):
    """Response for /import/preview endpoint."""
    total_rows: int
    errors: List[str] = []
    preview: List[Dict[str, Any]] = []

class QuestionPreviewItem(BaseModel):
    order: int
    text: str
    answers_count: int

class QuestionnairePreviewItem(BaseModel):
    wound_type: str
    title: str
    description: str = ""
    is_active: bool
    total_questions: int
    questions_preview: List[QuestionPreviewItem] = []

class FullImportPreviewResponse(BaseModel):
    """Response for /import/full/preview endpoint."""
    total_questionnaires: int
    errors: List[str] = []
    preview: List[QuestionnairePreviewItem] = []

class ImportResultItem(BaseModel):
    questionnaire_id: str
    title: str
    wound_type: str
    is_active: bool = False

class SingleImportResponse(BaseModel):
    """Response for /import/full endpoint."""
    imported: int
    questionnaire_id: str
    title: str
    wound_type: str
    errors: List[str] = []

class BulkImportResponse(BaseModel):
    """Response for /import/bulk endpoint."""
    imported: int
    questionnaires: List[ImportResultItem] = []
    errors: List[str] = []

class FileResultItem(BaseModel):
    filename: Optional[str] = None
    status: str
    message: str
    questionnaires: Optional[List[Any]] = None
    questionnaires_count: Optional[int] = None

class BulkFilesImportResponse(BaseModel):
    """Response for /import/bulk-files endpoint."""
    imported: int
    questionnaires: List[ImportResultItem] = []
    file_results: List[FileResultItem] = []
    errors: List[str] = []


# ─── Bulk Delete Schemas ─────────────────────────────────────────────────────

class BulkDeleteRequest(BaseModel):
    """Request for bulk delete endpoint."""
    ids: List[UUID] = Field(..., min_length=1, description="Danh sách ID bộ câu hỏi cần xóa")

class BulkDeleteResponse(BaseModel):
    """Response for bulk delete endpoint."""
    deleted: int
    message: str
