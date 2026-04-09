from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException
from datetime import datetime, timezone
from sqlalchemy import select, update

from app.modules.questionnaires.repository import QuestionnaireRepository
from app.modules.questionnaires.models import Questionnaire, Question, AnswerOption
from app.modules.questionnaires.schemas import (
    QuestionnaireCreate, QuestionnaireUpdate,
    QuestionCreate, QuestionUpdate,
    AnswerOptionCreate, AnswerOptionUpdate
)

def _current_timestamp() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class QuestionnaireService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = QuestionnaireRepository(session)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    async def _deactivate_others(self, wound_type: str, exclude_id: Optional[UUID] = None):
        """Deactivate all questionnaires with same wound_type except exclude_id."""
        stmt = (
            update(Questionnaire)
            .where(
                Questionnaire.wound_type == wound_type,
                Questionnaire.is_active == True,
            )
        )
        if exclude_id:
            stmt = stmt.where(Questionnaire.questionnaire_id != exclude_id)
        stmt = stmt.values(is_active=False, updated_at=_current_timestamp())
        await self.session.execute(stmt)

    # ─── Questionnaire CRUD ───────────────────────────────────────────────────

    async def get_all(self) -> List[Questionnaire]:
        return await self.repo.get_all()

    async def get_by_wound_type(self, wound_type: str) -> Optional[Questionnaire]:
        return await self.repo.get_active_by_wound_type(wound_type)

    async def get_by_id(self, q_id: UUID) -> Questionnaire:
        q = await self.repo.get_by_id(q_id)
        if not q:
            raise HTTPException(status_code=404, detail="Questionnaire not found")
        return q

    async def create_questionnaire(self, data: QuestionnaireCreate) -> Questionnaire:
        # If creating as active → deactivate others for same wound_type first
        if data.is_active:
            await self._deactivate_others(data.wound_type)

        q = Questionnaire(
            wound_type=data.wound_type,
            title=data.title,
            description=data.description,
            is_active=data.is_active
        )
        self.repo.create(q)

        if data.questions:
            for q_data in data.questions:
                question = Question(
                    question_text=q_data.question_text,
                    order_index=q_data.order_index,
                    is_multiple_choice=q_data.is_multiple_choice,
                    is_active=q_data.is_active,
                    questionnaire=q
                )
                self.repo.create(question)
                if q_data.answers:
                    for a_data in q_data.answers:
                        ans = AnswerOption(
                            answer_text=a_data.answer_text,
                            triage_level=a_data.triage_level,
                            icon_or_color=a_data.icon_or_color,
                            order_index=a_data.order_index,
                            metadata_tags=a_data.metadata_tags,
                            question=question
                        )
                        self.repo.create(ans)

        await self.session.commit()
        await self.session.refresh(q)
        return await self.repo.get_by_id(q.questionnaire_id)

    async def update_questionnaire(self, q_id: UUID, data: QuestionnaireUpdate) -> Questionnaire:
        q = await self.get_by_id(q_id)

        if data.title is not None:
            q.title = data.title
        if data.description is not None:
            q.description = data.description

        # If activating this → deactivate all others with same wound_type
        if data.is_active is True and not q.is_active:
            await self._deactivate_others(q.wound_type, exclude_id=q_id)
            q.is_active = True
        elif data.is_active is not None:
            q.is_active = data.is_active

        q.updated_at = _current_timestamp()
        await self.session.commit()
        await self.session.refresh(q)
        return q

    async def activate_questionnaire(self, q_id: UUID) -> Questionnaire:
        """Promote this questionnaire to active, deactivating all others for same wound_type."""
        q = await self.get_by_id(q_id)
        if q.is_active:
            return q  # Already active, no-op

        await self._deactivate_others(q.wound_type, exclude_id=q_id)
        q.is_active = True
        q.updated_at = _current_timestamp()
        await self.session.commit()
        await self.session.refresh(q)
        return q

    async def delete_questionnaire(self, q_id: UUID):
        q = await self.get_by_id(q_id)
        await self.repo.delete(q)
        await self.session.commit()

    # ─── Question CRUD ─────────────────────────────────────────────────────────

    async def add_question(self, q_id: UUID, data: QuestionCreate) -> Question:
        q = await self.get_by_id(q_id)
        question = Question(
            question_text=data.question_text,
            order_index=data.order_index,
            is_multiple_choice=data.is_multiple_choice,
            is_active=data.is_active,
            questionnaire_id=q.questionnaire_id
        )
        self.repo.create(question)
        if data.answers:
            for a_data in data.answers:
                ans = AnswerOption(
                    answer_text=a_data.answer_text,
                    triage_level=a_data.triage_level,
                    icon_or_color=a_data.icon_or_color,
                    order_index=a_data.order_index,
                    metadata_tags=a_data.metadata_tags,
                    question=question
                )
                self.repo.create(ans)

        q.updated_at = _current_timestamp()
        await self.session.commit()
        await self.session.refresh(question)
        return await self.repo.get_question(question.question_id)

    async def update_question(self, question_id: UUID, data: QuestionUpdate) -> Question:
        question = await self.repo.get_question(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        if data.question_text is not None:
            question.question_text = data.question_text
        if data.order_index is not None:
            question.order_index = data.order_index
        if data.is_multiple_choice is not None:
            question.is_multiple_choice = data.is_multiple_choice
        if data.is_active is not None:
            question.is_active = data.is_active

        question.updated_at = _current_timestamp()
        await self.session.commit()
        await self.session.refresh(question)
        return question

    async def delete_question(self, question_id: UUID):
        question = await self.repo.get_question(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        await self.repo.delete(question)
        await self.session.commit()

    # ─── Answer CRUD ───────────────────────────────────────────────────────────

    async def add_answer(self, question_id: UUID, data: AnswerOptionCreate) -> AnswerOption:
        question = await self.repo.get_question(question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        ans = AnswerOption(
            answer_text=data.answer_text,
            triage_level=data.triage_level,
            icon_or_color=data.icon_or_color,
            order_index=data.order_index,
            metadata_tags=data.metadata_tags,
            question_id=question_id
        )
        self.repo.create(ans)
        await self.session.commit()
        await self.session.refresh(ans)
        return ans

    async def update_answer(self, answer_id: UUID, data: AnswerOptionUpdate) -> AnswerOption:
        ans = await self.repo.get_answer(answer_id)
        if not ans:
            raise HTTPException(status_code=404, detail="Answer not found")

        if data.answer_text is not None:
            ans.answer_text = data.answer_text
        if data.triage_level is not None:
            ans.triage_level = data.triage_level
        if data.icon_or_color is not None:
            ans.icon_or_color = data.icon_or_color
        if data.order_index is not None:
            ans.order_index = data.order_index
        if data.metadata_tags is not None:
            ans.metadata_tags = data.metadata_tags

        ans.updated_at = _current_timestamp()
        await self.session.commit()
        await self.session.refresh(ans)
        return ans

    async def delete_answer(self, answer_id: UUID):
        ans = await self.repo.get_answer(answer_id)
        if not ans:
            raise HTTPException(status_code=404, detail="Answer not found")
        await self.repo.delete(ans)
        await self.session.commit()

    # ─── Import from CSV/Excel ─────────────────────────────────────────────────

    async def import_questions_from_data(
        self, q_id: UUID, rows: list[dict]
    ) -> Questionnaire:
        """
        Import questions+answers from parsed rows.
        rows format: [{question_order, question_text, is_multiple_choice, answer_text, triage_level}, ...]
        """
        q = await self.get_by_id(q_id)

        # Group by question_order
        from collections import OrderedDict
        questions_map: dict[int, dict] = OrderedDict()
        for row in rows:
            order = int(row.get("question_order", 1))
            if order not in questions_map:
                mc_val = str(row.get("is_multiple_choice", "false")).lower()
                questions_map[order] = {
                    "question_text": str(row["question_text"]).strip(),
                    "is_multiple_choice": mc_val in ("true", "1", "yes"),
                    "answers": []
                }
            answer_text = str(row.get("answer_text", "")).strip()
            triage = str(row.get("triage_level", "green")).strip().lower()
            if triage not in ("green", "yellow", "red"):
                triage = "green"
            if answer_text:
                questions_map[order]["answers"].append({
                    "answer_text": answer_text,
                    "triage_level": triage
                })

        # Create questions and answers
        for idx, (order, q_data) in enumerate(questions_map.items(), start=1):
            question = Question(
                question_text=q_data["question_text"],
                order_index=order,
                is_multiple_choice=q_data["is_multiple_choice"],
                is_active=True,
                questionnaire_id=q.questionnaire_id
            )
            self.repo.create(question)
            for ans_idx, ans_data in enumerate(q_data["answers"]):
                ans = AnswerOption(
                    answer_text=ans_data["answer_text"],
                    triage_level=ans_data["triage_level"],
                    order_index=ans_idx,
                    question=question
                )
                self.repo.create(ans)

        q.updated_at = _current_timestamp()
        await self.session.commit()
        return await self.repo.get_by_id(q.questionnaire_id)

    async def import_full_questionnaire(
        self, q_group: dict, auto_activate: bool = False
    ) -> Questionnaire:
        """
        Create a new Questionnaire from a parsed group dict (from parse_full_csv/excel).
        q_group: {wound_type, title, description, is_active, questions: [{...}]}
        If is_active=True or auto_activate=True → deactivate others with same wound_type.
        """
        is_active = q_group.get("is_active", False) or auto_activate

        if is_active:
            await self._deactivate_others(q_group["wound_type"])

        q = Questionnaire(
            wound_type=q_group["wound_type"],
            title=q_group["title"],
            description=q_group.get("description") or None,
            is_active=is_active,
        )
        self.repo.create(q)

        for q_data in q_group.get("questions", []):
            question = Question(
                question_text=q_data["question_text"],
                order_index=q_data["order_index"],
                is_multiple_choice=q_data["is_multiple_choice"],
                is_active=True,
                questionnaire=q,
            )
            self.repo.create(question)
            for ans_idx, ans_data in enumerate(q_data.get("answers", [])):
                ans = AnswerOption(
                    answer_text=ans_data["answer_text"],
                    triage_level=ans_data["triage_level"],
                    order_index=ans_idx,
                    question=question,
                )
                self.repo.create(ans)

        await self.session.commit()
        await self.session.refresh(q)
        return await self.repo.get_by_id(q.questionnaire_id)

    async def import_bulk_questionnaires(
        self, q_groups: list[dict], auto_activate: bool = False
    ) -> list[Questionnaire]:
        """
        Import multiple questionnaires from a list of parsed group dicts.
        For each wound_type, the LAST questionnaire with is_active=True wins activation.
        """
        results = []
        for group in q_groups:
            q = await self.import_full_questionnaire(group, auto_activate=auto_activate)
            results.append(q)
        return results

    # ─── Coverage / Gaps ───────────────────────────────────────────────────────

    async def get_coverage(self) -> dict:
        """
        Return coverage status for all canonical wound types.
        Shows which wound types have an active questionnaire and which don't.
        """
        from app.modules.questionnaires.import_export_service import VALID_WOUND_TYPES

        all_qs = await self.repo.get_all()

        # Build per-wound-type summary
        coverage = {}
        for wt in VALID_WOUND_TYPES:
            qs_for_type = [q for q in all_qs if q.wound_type == wt]
            active = [q for q in qs_for_type if q.is_active]
            coverage[wt] = {
                "wound_type": wt,
                "total": len(qs_for_type),
                "has_active": len(active) > 0,
                "active_title": active[0].title if active else None,
            }

        # Also include any custom wound_types not in VALID_WOUND_TYPES
        all_wts = {q.wound_type for q in all_qs}
        for wt in all_wts - VALID_WOUND_TYPES:
            qs_for_type = [q for q in all_qs if q.wound_type == wt]
            active = [q for q in qs_for_type if q.is_active]
            coverage[wt] = {
                "wound_type": wt,
                "total": len(qs_for_type),
                "has_active": len(active) > 0,
                "active_title": active[0].title if active else None,
            }

        return {
            "coverage": list(coverage.values()),
            "total_wound_types": len(coverage),
            "covered": sum(1 for v in coverage.values() if v["has_active"]),
            "uncovered": sum(1 for v in coverage.values() if not v["has_active"]),
        }

