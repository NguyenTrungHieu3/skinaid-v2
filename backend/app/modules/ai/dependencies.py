from typing import Annotated, Optional
from uuid import UUID

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.ai.mappers.response_mapper import ResponseMapper
from app.modules.ai.repository.model_repository import ModelRepository
from app.modules.ai.repository.wound_analysis_repository import WoundAnalysisRepository
from app.modules.ai.services.analysis_orchestration_service import AnalysisOrchestrationService
from app.modules.ai.services.image_processing_service import ImageProcessingService
from app.modules.ai.services.model_service import ModelService
from app.modules.ai.services.model_storage_service import get_storage_service
from app.modules.ai.services.wound_ai_service import WoundAIService
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.audit.audit_repository import AuditRepository
from app.modules.audit.services.audit_service import AuditService
from app.modules.firstaid.repository import FirstAidRepository
from app.modules.firstaid.service import FirstAidService
from app.modules.guest.repository import GuestRepository
from app.modules.guest.service import GuestService
from app.shared.exceptions.base import BadRequestError
from app.shared.services.file_service import FileService
from app.shared.validators.file_validator import FileValidator


async def get_guest_session_id(
    guest_session_id: Optional[str] = Cookie(None, alias="guest_session_id"),
    x_guest_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> Optional[UUID]:
    session_str = guest_session_id or x_guest_session_id
    if session_str:
        try:
            return UUID(session_str)
        except ValueError:
            raise BadRequestError(
                message="Invalid guest_session_id format",
                details={"provided_value": session_str},
            )
    return None


def get_wound_analysis_repository(db: AsyncSession = Depends(get_db)) -> WoundAnalysisRepository:
    return WoundAnalysisRepository(db)


def get_wound_analysis_service(
    repository: WoundAnalysisRepository = Depends(get_wound_analysis_repository),
    db: AsyncSession = Depends(get_db),
) -> WoundAnalysisService:
    firstaid_repo = FirstAidRepository(db)
    firstaid_service = FirstAidService(firstaid_repo, db)
    return WoundAnalysisService(repository=repository, first_aid_service=firstaid_service)


WoundAnalysisRepo = Annotated[WoundAnalysisRepository, Depends(get_wound_analysis_repository)]
WoundAnalysisSvc = Annotated[WoundAnalysisService, Depends(get_wound_analysis_service)]


def get_image_processing_service(
    analysis_service: WoundAnalysisService = Depends(get_wound_analysis_service),
) -> ImageProcessingService:
    return ImageProcessingService(
        analysis_service=analysis_service,
        ai_service=WoundAIService(),
        file_service=FileService(),
        validator=FileValidator(),
        response_mapper=ResponseMapper(),
    )


ImageProcessingSvc = Annotated[ImageProcessingService, Depends(get_image_processing_service)]


def get_analysis_orchestration_service(
    db: AsyncSession = Depends(get_db),
    image_service: ImageProcessingService = Depends(get_image_processing_service),
) -> AnalysisOrchestrationService:
    guest_service = GuestService(GuestRepository(db), db)
    audit_service = AuditService(AuditRepository(db))
    return AnalysisOrchestrationService(
        image_service=image_service,
        guest_service=guest_service,
        audit_service=audit_service,
        db=db,
    )


OrchestrationSvc = Annotated[AnalysisOrchestrationService, Depends(get_analysis_orchestration_service)]


def get_model_repository(db: AsyncSession = Depends(get_db)) -> ModelRepository:
    return ModelRepository(db)


def get_model_service(
    db: AsyncSession = Depends(get_db),
    repository: ModelRepository = Depends(get_model_repository),
) -> ModelService:
    audit_service = AuditService(AuditRepository(db))
    return ModelService(
        db=db,
        repository=repository,
        audit_service=audit_service,
        storage_service=get_storage_service(),
    )


ModelRepo = Annotated[ModelRepository, Depends(get_model_repository)]
ModelSvc = Annotated[ModelService, Depends(get_model_service)]


def get_response_mapper() -> ResponseMapper:
    return ResponseMapper()


ResponseMapperDep = Annotated[ResponseMapper, Depends(get_response_mapper)]
