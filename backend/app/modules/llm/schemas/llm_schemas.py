from __future__ import annotations

from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Wound type / severity constants
VALID_WOUND_TYPES = ["abrasion", "bruise", "burn", "cut", "acne", "fungal", "psoriasis"]
VALID_SEVERITIES = ["mild", "moderate", "severe"]


# Request

class LLMSynthesizeRequest(BaseModel):
    """Input cho B5 synthesis — wound_type + severity + optional questionnaire answers."""

    analysis_id: Optional[UUID] = Field(
        default=None,
        description="UUID của analysis — nếu cung cấp, structured_guidance sẽ được lưu vào Detection.firstaid_snapshot sau synthesis",
    )
    wound_type: str = Field(
        ...,
        description="Loại vết thương từ AI result (abrasion, cut, burn, ...)",
        examples=["abrasion"],
    )
    severity: str = Field(
        ...,
        description="Mức độ nghiêm trọng (mild / moderate / severe)",
        examples=["mild"],
    )
    sub_type: Optional[str] = Field(
        None,
        description="Loại phụ — chỉ dùng cho burn (blister, skintear)",
        examples=["blister"],
    )
    user_description: Optional[str] = Field(
        default="",
        max_length=2000,
        description="Câu trả lời questionnaire của người dùng (optional — có thể bỏ qua khi chưa có questionnaire)",
        examples=["Bị trầy xước khi ngã xe, vết thương dài khoảng 3cm, chảy máu nhẹ"],
    )
    top_k_rag: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Số chunks RAG lấy từ Qdrant (1-10)",
    )


# Structured guidance — output JSON từ LLM đã parse

class StructuredGuidance(BaseModel):
    """Hướng dẫn sơ cứu có cấu trúc — parse từ JSON output của LLM."""

    title: str = Field(default="Hướng dẫn sơ cứu")
    steps: List[str] = Field(default_factory=list)
    dos: List[str] = Field(default_factory=list)
    donts: List[str] = Field(default_factory=list)
    supplies_needed: List[str] = Field(default_factory=list)
    estimated_healing_time: Optional[str] = None


# Internal context (dùng trong orchestrator, không expose ra API)

class DBGuideSnapshot(BaseModel):
    """Snapshot gọn của FirstAidGuide từ DB — chỉ dùng nội bộ orchestrator và prompt builder."""

    title: str
    steps: List[str] = Field(default_factory=list)
    dos: List[str] = Field(default_factory=list)
    donts: List[str] = Field(default_factory=list)
    supplies_needed: List[str] = Field(default_factory=list)
    estimated_healing_time: Optional[str] = None


class RAGChunkSnapshot(BaseModel):
    """Snapshot gọn của KnowledgeChunk từ RAG — chỉ giữ content + score."""

    content: str
    relevance_score: float


class SynthesisContext(BaseModel):
    """Context đầy đủ truyền vào PromptBuilder — tổng hợp DB lookup + RAG retrieval."""

    wound_type: str
    severity: str
    sub_type: Optional[str] = None
    user_description: str = ""

    db_guide: Optional[DBGuideSnapshot] = None        # None nếu DB không có guide
    rag_chunks: List[RAGChunkSnapshot] = Field(default_factory=list)


# Response

class LLMSynthesizeResponse(BaseModel):
    """Output của B5 synthesis sau B6 validation — source='llm' nếu consistent, 'db' nếu fallback."""

    guidance: str = Field(
        ...,
        description="Nội dung hướng dẫn sơ cứu tổng hợp",
    )
    source: Literal["llm", "db"] = Field(
        ...,
        description="B6: 'llm' nếu LLM consistent, 'db' nếu fallback về DB",
    )
    validated: bool = Field(
        ...,
        description="True nếu LLM consistent với DB guide (hoặc DB không có guide)",
    )
    db_guide_available: bool = Field(
        ...,
        description="True nếu DB có first-aid guide cho wound_type + severity này",
    )
    rag_chunks_used: int = Field(
        ...,
        ge=0,
        description="Số RAG chunks thực tế đã đưa vào prompt",
    )
    model_version: str = Field(
        ...,
        description="Model OpenAI đã dùng để synthesis",
        examples=["gpt-5-nano"],
    )
    tokens_used: int = Field(
        default=0,
        ge=0,
        description="Tổng tokens consumed (prompt + completion)",
    )
    processing_time_ms: int = Field(
        default=0,
        ge=0,
        description="Tổng thời gian xử lý kể từ lúc nhận request (ms)",
    )
    confidence_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Điểm tin cậy của LLM output (tỉ lệ keyword match vs DB guide)",
    )
    structured_guidance: Optional[StructuredGuidance] = Field(
        None,
        description="Hướng dẫn có cấu trúc (steps/dos/donts) parse từ LLM JSON output — None nếu parse thất bại",
    )
