from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.questionnaires.repository.questionnaire_repository import QuestionnaireRepository
from app.modules.questionnaires.services.questionnaire_service import QuestionnaireService


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_questionnaire_repository(db: DbSession) -> QuestionnaireRepository:
    return QuestionnaireRepository(db)


def get_questionnaire_service(
    db: DbSession,
    repository: QuestionnaireRepository = Depends(get_questionnaire_repository),
) -> QuestionnaireService:
    return QuestionnaireService(db=db, repository=repository)


QuestionnaireRepo = Annotated[QuestionnaireRepository, Depends(get_questionnaire_repository)]
QuestionnaireSvc  = Annotated[QuestionnaireService,    Depends(get_questionnaire_service)]
