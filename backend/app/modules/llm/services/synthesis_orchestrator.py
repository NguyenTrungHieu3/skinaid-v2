from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Final

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.repository.wound_analysis_repository import WoundAnalysisRepository
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.firstaid.repository import FirstAidRepository
from app.modules.firstaid.service import FirstAidService
from app.modules.llm.exceptions import LLMContextBuildError
from app.modules.llm.schemas.llm_schemas import (
    DBGuideSnapshot,
    LLMSynthesizeRequest,
    LLMSynthesizeResponse,
    RAGChunkSnapshot,
    StructuredGuidance,
    SynthesisContext,
)
from app.modules.llm.services.llm_service import LLMService
from app.modules.llm.services.config_resolver import resolve_llm_config
from app.modules.llm.services.prompt_builder import PromptBuilder
from app.modules.rag.services.qdrant_service import RetrievedChunk, qdrant_service
from app.core.config import settings

logger = logging.getLogger(__name__)

_B6_MATCH_THRESHOLD: Final[float] = 0.6
_B6_MIN_KEYWORDS: Final[int] = 3
_B6_MAX_KEYWORDS: Final[int] = 8


class SynthesisOrchestrator:
    """Orchestrator cho B5 → B6 pipeline: parallel I/O → prompt → LLM → validation."""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: LLMService,
        prompt_builder: PromptBuilder,
    ) -> None:
        self._db = db
        self._llm_service = llm_service
        self._prompt_builder = prompt_builder
        self._firstaid_service = FirstAidService(
            repository=FirstAidRepository(db), db=db
        )
        self._wound_analysis_service = WoundAnalysisService(
            repository=WoundAnalysisRepository(db),
            first_aid_service=self._firstaid_service,
        )

    # Public API

    async def synthesize(self, request: LLMSynthesizeRequest) -> LLMSynthesizeResponse:
        """Thực hiện toàn bộ B5 → B6 pipeline, trả về LLMSynthesizeResponse."""
        start_ms = time.monotonic()

        # ── Step 1: Parallel I/O
        context = await self._build_synthesis_context(request)

        # ── Step 2: Build messages
        try:
            messages = [
                {
                    "role": "system",
                    "content": self._prompt_builder.build_system_prompt(),
                },
                {
                    "role": "user",
                    "content": self._prompt_builder.build_user_prompt(context),
                },
            ]
        except Exception as exc:
            raise LLMContextBuildError(
                message="Không thể xây dựng prompt cho LLM",
                details={"error": str(exc)[:200]},
            ) from exc

        # ── Step 3: Resolve config from DB + check active/maintenance
        llm_cfg = await resolve_llm_config(self._db, "synthesis")

        # ── Step 4: Gọi LLM với config từ DB
        llm_output, tokens_used = await self._llm_service.call(
            messages,
            model=llm_cfg.model_name,
            temperature=llm_cfg.temperature,
            max_tokens=llm_cfg.max_tokens,
            config_key="synthesis",
        )

        # ── Step 5: B6 Validation
        validated, source, confidence = self._validate_b6(llm_output, context.db_guide)

        # ── Step 6: Chọn guidance cuối cùng
        if source == "db" and context.db_guide is not None:
            guidance = self._format_db_guide_as_text(context.db_guide)
            structured = self._build_structured_from_db(context.db_guide)
            logger.info(
                "[SynthesisOrchestrator] B6: LLM không consistent (confidence=%.2f) "
                "→ fallback DB guide.",
                confidence,
            )
        else:
            guidance = llm_output
            structured = self._parse_structured_output(llm_output)
            if structured is None:
                logger.warning(
                    "[SynthesisOrchestrator] JSON parse thất bại — structured_guidance=None."
                )
            logger.info(
                "[SynthesisOrchestrator] B6: LLM consistent (confidence=%.2f) "
                "→ dùng LLM output.",
                confidence,
            )

        processing_time_ms = int((time.monotonic() - start_ms) * 1000)

        # ── Step 6: Persist structured_guidance vào Detection.firstaid_snapshot
        if request.analysis_id is not None and structured is not None:
            try:
                rows = await self._wound_analysis_service.persist_llm_guidance(
                    analysis_id=request.analysis_id,
                    wound_type=request.wound_type,
                    severity=request.severity,
                    structured_guidance=structured.model_dump(),
                )
                logger.info(
                    "[SynthesisOrchestrator] Persisted LLM guidance → %d detection(s) updated "
                    "(analysis_id=%s, wound_type=%s, severity=%s).",
                    rows,
                    request.analysis_id,
                    request.wound_type,
                    request.severity,
                )
            except Exception as exc:
                logger.warning(
                    "[SynthesisOrchestrator] Persist LLM guidance thất bại (non-blocking): %s",
                    str(exc)[:200],
                )

        return LLMSynthesizeResponse(
            guidance=guidance,
            source=source,
            validated=validated,
            db_guide_available=context.db_guide is not None,
            rag_chunks_used=len(context.rag_chunks),
            model_version=settings.LLM_MODEL,
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms,
            confidence_score=round(confidence, 3),
            structured_guidance=structured,
        )

    async def _build_synthesis_context(
        self, request: LLMSynthesizeRequest
    ) -> SynthesisContext:
        """Chạy song song RAG retrieval và DB lookup, lỗi từng task log warning không block flow."""
        rag_query = (
            f"{request.wound_type} {request.severity} {request.user_description}"
        )

        rag_task = qdrant_service.hybrid_search(
            query=rag_query,
            top_k=request.top_k_rag,
        )
        db_task = self._firstaid_service.get_guide(
            wound_type=request.wound_type,
            severity=request.severity,
            sub_type=request.sub_type,
        )

        rag_result, db_result = await asyncio.gather(
            rag_task, db_task, return_exceptions=True
        )

        rag_chunks: list[RAGChunkSnapshot] = []
        if isinstance(rag_result, Exception):
            logger.warning(
                "[SynthesisOrchestrator] RAG retrieval thất bại (%s). Tiếp tục không có RAG.",
                str(rag_result)[:150],
            )
            await self._log_system_error(
                action="rag_error",
                error_message=f"RAG retrieval failed: {str(rag_result)[:300]}",
                details={"error_type": type(rag_result).__name__},
            )
        elif isinstance(rag_result, list):
            rag_chunks = [
                RAGChunkSnapshot(
                    content=chunk.content,
                    relevance_score=chunk.score,
                )
                for chunk in rag_result
                if isinstance(chunk, RetrievedChunk)
            ]
            logger.info(
                "[SynthesisOrchestrator] RAG: %d chunks retrieved.", len(rag_chunks)
            )

        db_guide_snapshot: DBGuideSnapshot | None = None
        if isinstance(db_result, Exception):
            logger.warning(
                "[SynthesisOrchestrator] DB lookup thất bại (%s). Tiếp tục không có DB guide.",
                str(db_result)[:150],
            )
            await self._log_system_error(
                action="llm_api_error",
                error_message=f"DB guide lookup failed: {str(db_result)[:300]}",
                details={"error_type": type(db_result).__name__},
            )
        elif db_result is not None:
            db_guide_snapshot = DBGuideSnapshot(
                title=db_result.title,
                steps=db_result.extract_list(db_result.steps),
                dos=db_result.extract_list(db_result.dos),
                donts=db_result.extract_list(db_result.donts),
                supplies_needed=db_result.extract_list(db_result.supplies_needed),
                estimated_healing_time=db_result.estimated_healing_time,
            )
            logger.info(
                "[SynthesisOrchestrator] DB guide found: '%s'.", db_guide_snapshot.title
            )
        else:
            logger.info(
                "[SynthesisOrchestrator] DB guide: không có guide cho %s/%s.",
                request.wound_type,
                request.severity,
            )

        return SynthesisContext(
            wound_type=request.wound_type,
            severity=request.severity,
            sub_type=request.sub_type,
            user_description=request.user_description or "",
            db_guide=db_guide_snapshot,
            rag_chunks=rag_chunks,
        )

    def _validate_b6(
        self,
        llm_output: str,
        db_guide: DBGuideSnapshot | None,
    ) -> tuple[bool, str, float]:
        """Keyword match LLM output vs DB guide — ratio ≥ threshold → (True, "llm"), else (False, "db")."""
        if db_guide is None:
            return True, "llm", 1.0

        keywords = self._extract_keywords(db_guide)

        if not keywords:
            return True, "llm", 1.0

        llm_lower = llm_output.lower()
        matched = sum(1 for kw in keywords if kw in llm_lower)
        ratio = matched / len(keywords)

        logger.debug(
            "[SynthesisOrchestrator] B6: %d/%d keywords matched (ratio=%.2f, threshold=%.2f).",
            matched,
            len(keywords),
            ratio,
            _B6_MATCH_THRESHOLD,
        )

        if ratio >= _B6_MATCH_THRESHOLD:
            return True, "llm", ratio
        else:
            return False, "db", ratio

    def _extract_keywords(self, db_guide: DBGuideSnapshot) -> list[str]:
        """Extract từ khóa từ steps + dos: tokenize, deduplicate, min 3 / max 8 keywords."""
        source_items = db_guide.steps + db_guide.dos
        if not source_items:
            return []

        raw_tokens: list[str] = []
        for item in source_items:
            tokens = re.findall(r"[a-zA-ZÀ-ỹà-ỹ]{4,}", item.lower())
            raw_tokens.extend(tokens)

        seen: set[str] = set()
        keywords: list[str] = []
        for token in raw_tokens:
            if token not in seen:
                seen.add(token)
                keywords.append(token)
            if len(keywords) >= _B6_MAX_KEYWORDS:
                break

        if len(keywords) < _B6_MIN_KEYWORDS:
            return []

        return keywords

    @staticmethod
    def _parse_structured_output(llm_text: str) -> StructuredGuidance | None:
        """Extract và parse JSON từ LLM output, trả None nếu thất bại."""
        # LLM đôi khi bọc JSON trong ```json ... ```
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", llm_text, re.DOTALL)
        if json_match:
            raw_json = json_match.group(1)
        else:
            # Thử tìm bare JSON object
            brace_match = re.search(r"\{.*\}", llm_text, re.DOTALL)
            raw_json = brace_match.group(0) if brace_match else llm_text.strip()

        try:
            data = json.loads(raw_json)
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "[SynthesisOrchestrator] Không parse được JSON từ LLM output. "
                "Preview: %s", llm_text[:200]
            )
            return None

        if not isinstance(data, dict):
            return None

        def _to_str_list(val: object) -> list[str]:
            if isinstance(val, list):
                return [str(item) for item in val if item]
            return []

        return StructuredGuidance(
            title=str(data.get("title", "Hướng dẫn sơ cứu")),
            steps=_to_str_list(data.get("steps")),
            dos=_to_str_list(data.get("dos")),
            donts=_to_str_list(data.get("donts")),
            supplies_needed=_to_str_list(data.get("supplies_needed")),
            estimated_healing_time=data.get("estimated_healing_time") or None,
        )

    @staticmethod
    def _build_structured_from_db(db_guide: DBGuideSnapshot) -> StructuredGuidance:
        """Tạo StructuredGuidance từ DBGuideSnapshot khi B6 fallback về DB."""
        return StructuredGuidance(
            title=db_guide.title,
            steps=db_guide.steps,
            dos=db_guide.dos,
            donts=db_guide.donts,
            supplies_needed=db_guide.supplies_needed,
            estimated_healing_time=db_guide.estimated_healing_time,
        )

    @staticmethod
    def _format_db_guide_as_text(db_guide: DBGuideSnapshot) -> str:
        """Format DBGuideSnapshot thành markdown text khi B6 fallback về source='db'."""
        lines: list[str] = [f"**{db_guide.title}**\n"]

        if db_guide.steps:
            lines.append("**Các bước sơ cứu:**")
            for i, step in enumerate(db_guide.steps, 1):
                lines.append(f"{i}. {step}")

        if db_guide.dos:
            lines.append("\n**Nên làm:**")
            for item in db_guide.dos:
                lines.append(f"• {item}")

        if db_guide.donts:
            lines.append("\n**Không nên làm:**")
            for item in db_guide.donts:
                lines.append(f"• {item}")

        if db_guide.supplies_needed:
            lines.append("\n**Vật tư cần thiết:**")
            for item in db_guide.supplies_needed:
                lines.append(f"• {item}")

        if db_guide.estimated_healing_time:
            lines.append(
                f"\n**Thời gian hồi phục ước tính:** {db_guide.estimated_healing_time}"
            )

        return "\n".join(lines)
