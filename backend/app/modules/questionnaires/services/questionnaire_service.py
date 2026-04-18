from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import update
from collections import OrderedDict

from app.modules.questionnaires.repository.questionnaire_repository import QuestionnaireRepository
from app.modules.questionnaires.models.questionnaire import Questionnaire
from app.modules.questionnaires.models.question import Question
from app.modules.questionnaires.models.answer_option import AnswerOption
from app.modules.questionnaires.schemas.api import (
    QuestionnaireCreate, QuestionnaireUpdate,
    QuestionCreate, QuestionUpdate,
    AnswerOptionCreate, AnswerOptionUpdate
)
from app.modules.questionnaires.exceptions import (
    QuestionnaireNotFoundError,
    QuestionNotFoundError,
    AnswerNotFoundError,
)


def _current_timestamp() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class QuestionnaireService:
    def __init__(self, db: AsyncSession, repository: QuestionnaireRepository):
        self.db = db
        self.repo = repository

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
        await self.db.execute(stmt)

    async def _get_questionnaire_or_raise(self, q_id: UUID) -> Questionnaire:
        """Get questionnaire by ID or raise QuestionnaireNotFoundError."""
        q = await self.repo.get_questionnaire_by_id(q_id)
        if not q:
            raise QuestionnaireNotFoundError(str(q_id))
        return q

    async def _get_question_or_raise(self, question_id: UUID) -> Question:
        """Get question by ID or raise QuestionNotFoundError."""
        question = await self.repo.get_question(question_id)
        if not question:
            raise QuestionNotFoundError(str(question_id))
        return question

    async def _get_answer_or_raise(self, answer_id: UUID) -> AnswerOption:
        """Get answer by ID or raise AnswerNotFoundError."""
        ans = await self.repo.get_answer(answer_id)
        if not ans:
            raise AnswerNotFoundError(str(answer_id))
        return ans

    # ─── Questionnaire CRUD ───────────────────────────────────────────────────

    async def get_all(self) -> List[Questionnaire]:
        return await self.repo.get_all()

    async def get_by_wound_type(self, wound_type: str) -> Optional[Questionnaire]:
        return await self.repo.get_active_by_wound_type(wound_type)

    async def get_by_id(self, q_id: UUID) -> Questionnaire:
        return await self._get_questionnaire_or_raise(q_id)

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
        await self.repo.create(q)

        if data.questions:
            for q_data in data.questions:
                question = Question(
                    question_text=q_data.question_text,
                    order_index=q_data.order_index,
                    is_multiple_choice=q_data.is_multiple_choice,
                    is_active=q_data.is_active,
                    questionnaire=q
                )
                await self.repo.create(question)
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
                        await self.repo.create(ans)

        await self.db.flush()
        await self.db.refresh(q)
        return await self.repo.get_questionnaire_by_id(q.questionnaire_id)

    async def update_questionnaire(self, q_id: UUID, data: QuestionnaireUpdate) -> Questionnaire:
        q = await self._get_questionnaire_or_raise(q_id)

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
        await self.db.flush()
        await self.db.refresh(q)
        return q

    async def activate_questionnaire(self, q_id: UUID) -> Questionnaire:
        """Promote this questionnaire to active, deactivating all others for same wound_type."""
        q = await self._get_questionnaire_or_raise(q_id)
        if q.is_active:
            return q  # Already active, no-op

        await self._deactivate_others(q.wound_type, exclude_id=q_id)
        q.is_active = True
        q.updated_at = _current_timestamp()
        await self.db.flush()
        await self.db.refresh(q)
        return q

    async def delete_questionnaire(self, q_id: UUID):
        q = await self._get_questionnaire_or_raise(q_id)
        await self.repo.delete(q)
        await self.db.flush()

    # ─── Question CRUD ─────────────────────────────────────────────────────────

    async def add_question(self, q_id: UUID, data: QuestionCreate) -> Question:
        q = await self._get_questionnaire_or_raise(q_id)
        question = Question(
            question_text=data.question_text,
            order_index=data.order_index,
            is_multiple_choice=data.is_multiple_choice,
            is_active=data.is_active,
            questionnaire_id=q.questionnaire_id
        )
        await self.repo.create(question)
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
                await self.repo.create(ans)

        q.updated_at = _current_timestamp()
        await self.db.flush()
        await self.db.refresh(question)
        return await self.repo.get_question(question.question_id)

    async def update_question(self, question_id: UUID, data: QuestionUpdate) -> Question:
        question = await self._get_question_or_raise(question_id)

        if data.question_text is not None:
            question.question_text = data.question_text
        if data.order_index is not None:
            question.order_index = data.order_index
        if data.is_multiple_choice is not None:
            question.is_multiple_choice = data.is_multiple_choice
        if data.is_active is not None:
            question.is_active = data.is_active

        question.updated_at = _current_timestamp()
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def delete_question(self, question_id: UUID):
        question = await self._get_question_or_raise(question_id)
        await self.repo.delete(question)
        await self.db.flush()

    # ─── Answer CRUD ───────────────────────────────────────────────────────────

    async def add_answer(self, question_id: UUID, data: AnswerOptionCreate) -> AnswerOption:
        await self._get_question_or_raise(question_id)

        ans = AnswerOption(
            answer_text=data.answer_text,
            triage_level=data.triage_level,
            icon_or_color=data.icon_or_color,
            order_index=data.order_index,
            metadata_tags=data.metadata_tags,
            question_id=question_id
        )
        await self.repo.create(ans)
        await self.db.flush()
        await self.db.refresh(ans)
        return ans

    async def update_answer(self, answer_id: UUID, data: AnswerOptionUpdate) -> AnswerOption:
        ans = await self._get_answer_or_raise(answer_id)

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
        await self.db.flush()
        await self.db.refresh(ans)
        return ans

    async def delete_answer(self, answer_id: UUID):
        ans = await self._get_answer_or_raise(answer_id)
        await self.repo.delete(ans)
        await self.db.flush()

    # ─── Import from CSV/Excel ─────────────────────────────────────────────────

    async def import_questions_from_data(
        self, q_id: UUID, rows: list[dict]
    ) -> Questionnaire:
        """
        Import questions+answers from parsed rows.
        rows format: [{question_order, question_text, is_multiple_choice, answer_text, triage_level}, ...]
        """
        q = await self._get_questionnaire_or_raise(q_id)

        # Group by question_order
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
        for _idx, (order, q_data) in enumerate(questions_map.items(), start=1):
            question = Question(
                question_text=q_data["question_text"],
                order_index=order,
                is_multiple_choice=q_data["is_multiple_choice"],
                is_active=True,
                questionnaire_id=q.questionnaire_id
            )
            await self.repo.create(question)
            for ans_idx, ans_data in enumerate(q_data["answers"]):
                ans = AnswerOption(
                    answer_text=ans_data["answer_text"],
                    triage_level=ans_data["triage_level"],
                    order_index=ans_idx,
                    question=question
                )
                await self.repo.create(ans)

        q.updated_at = _current_timestamp()
        await self.db.flush()
        return await self.repo.get_questionnaire_by_id(q.questionnaire_id)

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
        await self.repo.create(q)

        for q_data in q_group.get("questions", []):
            question = Question(
                question_text=q_data["question_text"],
                order_index=q_data["order_index"],
                is_multiple_choice=q_data["is_multiple_choice"],
                is_active=True,
                questionnaire=q,
            )
            await self.repo.create(question)
            for ans_idx, ans_data in enumerate(q_data.get("answers", [])):
                ans = AnswerOption(
                    answer_text=ans_data["answer_text"],
                    triage_level=ans_data["triage_level"],
                    order_index=ans_idx,
                    question=question,
                )
                await self.repo.create(ans)

        await self.db.flush()
        await self.db.refresh(q)
        return await self.repo.get_questionnaire_by_id(q.questionnaire_id)

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
        from app.modules.questionnaires.services.import_service import VALID_WOUND_TYPES

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

    async def import_bulk_files(
        self, files_data: list[tuple[str, bytes]], auto_activate: bool = False
    ) -> dict:
        """
        Process multiple uploaded files for import.
        files_data: list of (filename, content_bytes) tuples.
        Returns {imported, questionnaires, file_results, errors}.
        """
        from app.modules.questionnaires.services.import_service import parse_full_file
        from app.modules.questionnaires.exceptions import ImportValidationError

        all_groups: list = []
        all_errors: list = []
        file_results: list = []

        for filename, content in files_data:
            try:
                try:
                    groups, errors = parse_full_file(filename, content)
                except ImportValidationError:
                    file_results.append({
                        "filename": filename,
                        "status": "error",
                        "message": "Định dạng không hỗ trợ (chỉ CSV hoặc Excel)",
                        "questionnaires": [],
                    })
                    continue

                if errors:
                    all_errors.extend([f"[{filename}] {e}" for e in errors])

                if not groups:
                    file_results.append({
                        "filename": filename,
                        "status": "error",
                        "message": "Không có dữ liệu hợp lệ trong file",
                        "questionnaires": [],
                    })
                    continue

                all_groups.extend(groups)
                file_results.append({
                    "filename": filename,
                    "status": "ok",
                    "message": f"Tìm thấy {len(groups)} bộ câu hỏi",
                    "questionnaires_count": len(groups),
                })
            except Exception as exc:
                file_results.append({
                    "filename": filename,
                    "status": "error",
                    "message": f"Lỗi đọc file: {type(exc).__name__}: {exc}",
                    "questionnaires": [],
                })

        results = []
        if all_groups:
            results = await self.import_bulk_questionnaires(all_groups, auto_activate=auto_activate)

        return {
            "imported": len(results),
            "questionnaires": results,
            "file_results": file_results,
            "errors": all_errors,
        }

    async def export_bulk(
        self, ids: list[str], fmt: str
    ) -> tuple[bytes, str, str]:
        """
        Export multiple questionnaires by IDs.
        Returns (file_bytes, filename, media_type).
        Raises QuestionnaireNotFoundError if no valid questionnaires found.
        """
        from app.modules.questionnaires.services import export_service as exp

        questionnaires = []
        for q_id in ids:
            try:
                q = await self.get_by_id(UUID(q_id))
                questionnaires.append(q)
            except Exception:
                pass  # skip invalid IDs

        if not questionnaires:
            raise QuestionnaireNotFoundError("Không tìm thấy bộ câu hỏi nào")

        count = len(questionnaires)
        if fmt == "csv":
            return exp.export_bulk_to_csv(questionnaires), f"questionnaires_export_{count}.csv", "text/csv"
        elif fmt == "excel":
            return exp.export_bulk_to_excel(questionnaires), f"questionnaires_export_{count}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif fmt == "docx":
            return exp.export_bulk_to_docx(questionnaires), f"questionnaires_export_{count}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:  # pdf
            return exp.export_bulk_to_pdf(questionnaires), f"questionnaires_export_{count}.pdf", "application/pdf"

