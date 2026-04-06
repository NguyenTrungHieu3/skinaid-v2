from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID

from app.modules.questionnaires.models import Questionnaire, Question, AnswerOption

class QuestionnaireRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[Questionnaire]:
        stmt = select(Questionnaire).options(
            selectinload(Questionnaire.questions).selectinload(Question.answers)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_wound_type(self, wound_type: str) -> Optional[Questionnaire]:
        """Get first questionnaire for wound_type (legacy - use get_active_by_wound_type)."""
        stmt = select(Questionnaire).where(Questionnaire.wound_type == wound_type).options(
            selectinload(Questionnaire.questions).selectinload(Question.answers)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_by_wound_type(self, wound_type: str) -> Optional[Questionnaire]:
        """Get the single active questionnaire for a wound_type."""
        stmt = (
            select(Questionnaire)
            .where(Questionnaire.wound_type == wound_type, Questionnaire.is_active == True)
            .options(selectinload(Questionnaire.questions).selectinload(Question.answers))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all_by_wound_type(self, wound_type: str) -> List[Questionnaire]:
        """Get all questionnaires for a wound_type (active + draft)."""
        stmt = (
            select(Questionnaire)
            .where(Questionnaire.wound_type == wound_type)
            .options(selectinload(Questionnaire.questions).selectinload(Question.answers))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_id(self, q_id: UUID) -> Optional[Questionnaire]:
        stmt = select(Questionnaire).where(Questionnaire.questionnaire_id == q_id).options(
            selectinload(Questionnaire.questions).selectinload(Question.answers)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    def create(self, entity):
        self.session.add(entity)

    async def delete(self, entity):
        await self.session.delete(entity)

    async def get_question(self, question_id: UUID) -> Optional[Question]:
        stmt = select(Question).where(Question.question_id == question_id).options(
            selectinload(Question.answers)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_answer(self, answer_id: UUID) -> Optional[AnswerOption]:
        stmt = select(AnswerOption).where(AnswerOption.answer_id == answer_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
