from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.questionnaires.repository.questionnaire_repository import (
    QuestionnaireRepository,
)
from app.modules.questionnaires.services.user_questionnaire_service import (
    UserQuestionnaireService,
)


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_questionnaire_repository_for_user(db: DbSession) -> QuestionnaireRepository:
    return QuestionnaireRepository(db)


def get_user_questionnaire_service(
    db: DbSession,
    repository: QuestionnaireRepository = Depends(get_questionnaire_repository_for_user),
) -> UserQuestionnaireService:
    return UserQuestionnaireService(db=db, repository=repository)


UserQuestionnaireSvc = Annotated[
    UserQuestionnaireService, Depends(get_user_questionnaire_service)
]
