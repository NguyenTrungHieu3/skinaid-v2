from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.questionnaires.repository.questionnaire_repository import (
    QuestionnaireRepository,
)
from app.modules.questionnaires.models.questionnaire import Questionnaire
from app.modules.questionnaires.models.answer_option import AnswerOption
from app.modules.questionnaires.exceptions import (
    QuestionNotFoundError,
    AnswerNotFoundError,
)
from app.modules.questionnaires.schemas.user_api import (
    WoundDetectionInput,
    ResolvedQuestionnaireItem,
    MissingQuestionnaireItem,
    ResolveQuestionnairesResponse,
    AnswerSelectionInput,
    AnswerSelectionView,
    SubmitWoundResponseRequest,
    SubmitWoundResponseResponse,
    SynthesisSummary,
    SEVERITY_ORDER,
    TRIAGE_ORDER,
    ALLOWED_TRIAGES,
)

logger = logging.getLogger(__name__)


DedupeKey = Tuple[str, Optional[str]]


def _build_wound_key(wound_type: str, subtype: Optional[str]) -> str:
    """Composite lookup key: subtype present → "{wound_type}_{subtype}", else wound_type."""
    if subtype:
        return f"{wound_type}_{subtype}"
    return wound_type


def _pick_severity(severities: List[Optional[str]]) -> Optional[str]:
    ranked = [s for s in severities if s is not None]
    if not ranked:
        return None
    return max(ranked, key=lambda s: SEVERITY_ORDER.get(s, 0))


def _pick_triage(levels: List[str]) -> str:
    ranked = [t for t in levels if t in ALLOWED_TRIAGES]
    if not ranked:
        return "green"
    return max(ranked, key=lambda t: TRIAGE_ORDER.get(t, 0))


class UserQuestionnaireService:
    """User-facing: resolve questionnaires from AI detections + submit answers."""

    def __init__(
        self,
        db: AsyncSession,
        repository: QuestionnaireRepository,
    ) -> None:
        self.db = db
        self.repo = repository

    async def resolve_questionnaires(
        self, detections: List[WoundDetectionInput]
    ) -> ResolveQuestionnairesResponse:
        grouped: Dict[DedupeKey, List[WoundDetectionInput]] = {}
        for d in detections:
            key: DedupeKey = (d.wound_type, d.subtype)
            grouped.setdefault(key, []).append(d)

        resolved: List[ResolvedQuestionnaireItem] = []
        missing: List[MissingQuestionnaireItem] = []

        for (wound_type, subtype), items in grouped.items():
            severities = [i.severity for i in items]
            top_severity = _pick_severity(severities)
            rep = next((i for i in items if i.severity == top_severity), items[0])

            wound_key = _build_wound_key(wound_type, subtype)
            questionnaire: Optional[Questionnaire] = (
                await self.repo.get_active_by_wound_type(wound_key)
            )

            # Fallback: nếu composite key (vd: "burn_blister") không tìm thấy,
            # thử lại với wound_type thuần (vd: "burn").
            if questionnaire is None and subtype:
                questionnaire = await self.repo.get_active_by_wound_type(wound_type)

            if questionnaire is None:
                missing.append(
                    MissingQuestionnaireItem(
                        wound_type=wound_type,
                        subtype=subtype,
                        severity=top_severity,
                        detection_count=len(items),
                    )
                )
                continue

            resolved.append(
                ResolvedQuestionnaireItem(
                    wound_type=wound_type,
                    subtype=subtype,
                    severity=top_severity,
                    representative_detection_id=rep.detection_id,
                    detection_count=len(items),
                    questionnaire=questionnaire,
                )
            )

        return ResolveQuestionnairesResponse(
            questionnaires=resolved,
            missing=missing,
            total_unique_keys=len(grouped),
        )

    async def submit(
        self,
        payload: SubmitWoundResponseRequest,
        synthesize_fn=None,
    ) -> SubmitWoundResponseResponse:
        selection_views: List[AnswerSelectionView] = []
        all_triages: List[str] = []

        for sel in payload.answers:
            await self._validate_question_exists(sel.question_id)
            triage_levels = await self._validate_and_collect_triages(
                sel.question_id, sel.answer_ids
            )
            all_triages.extend(triage_levels)
            selection_views.append(
                AnswerSelectionView(
                    question_id=sel.question_id,
                    answer_ids=sel.answer_ids,
                    triage_levels=triage_levels,
                )
            )

        aggregated = _pick_triage(all_triages)

        syntheses: List[SynthesisSummary] = []
        if payload.forward_to_synthesis and synthesize_fn is not None:
            resolved = await self.resolve_questionnaires(payload.detections)
            user_desc = payload.user_description or ""
            for item in resolved.questionnaires:
                severity = item.severity or "mild"
                try:
                    summary = await synthesize_fn(
                        wound_type=item.wound_type,
                        subtype=item.subtype,
                        severity=severity,
                        user_description=user_desc,
                    )
                    if summary is not None:
                        syntheses.append(summary)
                except Exception as exc:
                    logger.exception(
                        "synthesis failed for %s/%s", item.wound_type, item.subtype
                    )
                    syntheses.append(
                        SynthesisSummary(
                            wound_type=item.wound_type,
                            subtype=item.subtype,
                            severity=severity,
                            source="db",
                            guidance="",
                            validated=False,
                            error=f"{type(exc).__name__}: {exc}",
                        )
                    )

        return SubmitWoundResponseResponse(
            aggregated_triage=aggregated,  # type: ignore[arg-type]
            selections=selection_views,
            syntheses=syntheses,
        )

    async def _validate_question_exists(self, question_id: UUID) -> None:
        q = await self.repo.get_question(question_id)
        if q is None:
            raise QuestionNotFoundError(str(question_id))

    async def _validate_and_collect_triages(
        self, question_id: UUID, answer_ids: List[UUID]
    ) -> List[str]:
        triages: List[str] = []
        for aid in answer_ids:
            ans: Optional[AnswerOption] = await self.repo.get_answer(aid)
            if ans is None or ans.question_id != question_id:
                raise AnswerNotFoundError(str(aid))
            triages.append(ans.triage_level)
        return triages
