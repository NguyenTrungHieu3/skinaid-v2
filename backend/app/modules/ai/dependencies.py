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
from app.modules.audit.dependencies import get_audit_service
from app.modules.audit.services.audit_service import AuditService
from app.modules.firstaid.dependencies import get_firstaid_service
from app.modules.firstaid.service import FirstAidService
from app.modules.guest.dependencies import get_guest_service
from app.modules.guest.service import GuestService
from app.modules.notifications.dependencies import get_notification_service
from app.modules.notifications.service import NotificationService
from app.shared.exceptions.base import BadRequestError
from app.shared.services.file_service import FileService
from app.shared.validators.file_validator import FileValidator


# ── Cookie/Header helpers ─────────────────────────────────────────────────────

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


# ── Stateless service factories ───────────────────────────────────────────────

def get_wound_ai_service() -> WoundAIService:
    return WoundAIService()


def get_file_service() -> FileService:
    return FileService()


def get_file_validator() -> FileValidator:
    return FileValidator()


def get_response_mapper() -> ResponseMapper:
    return ResponseMapper()


# ── Repository factories ──────────────────────────────────────────────────────

def get_wound_analysis_repository(db: AsyncSession = Depends(get_db)) -> WoundAnalysisRepository:
    return WoundAnalysisRepository(db)


def get_model_repository(db: AsyncSession = Depends(get_db)) -> ModelRepository:
    return ModelRepository(db)


# ── Service factories ─────────────────────────────────────────────────────────

def get_wound_analysis_service(
    repository: WoundAnalysisRepository = Depends(get_wound_analysis_repository),
    firstaid_service: FirstAidService = Depends(get_firstaid_service),
) -> WoundAnalysisService:
    return WoundAnalysisService(repository=repository, first_aid_service=firstaid_service)


def get_image_processing_service(
    analysis_service: WoundAnalysisService = Depends(get_wound_analysis_service),
    notification_service: NotificationService = Depends(get_notification_service),
    ai_service: WoundAIService = Depends(get_wound_ai_service),
    file_service: FileService = Depends(get_file_service),
    validator: FileValidator = Depends(get_file_validator),
    response_mapper: ResponseMapper = Depends(get_response_mapper),
) -> ImageProcessingService:
    return ImageProcessingService(
        analysis_service=analysis_service,
        ai_service=ai_service,
        file_service=file_service,
        validator=validator,
        response_mapper=response_mapper,
        notification_service=notification_service,
    )


def get_analysis_orchestration_service(
    db: AsyncSession = Depends(get_db),
    image_service: ImageProcessingService = Depends(get_image_processing_service),
    guest_service: GuestService = Depends(get_guest_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> AnalysisOrchestrationService:
    return AnalysisOrchestrationService(
        image_service=image_service,
        guest_service=guest_service,
        audit_service=audit_service,
        db=db,
    )


def get_model_service(
    db: AsyncSession = Depends(get_db),
    repository: ModelRepository = Depends(get_model_repository),
    audit_service: AuditService = Depends(get_audit_service),
) -> ModelService:
    return ModelService(
        db=db,
        repository=repository,
        audit_service=audit_service,
        storage_service=get_storage_service(),
    )


# ── Annotated shortcuts ───────────────────────────────────────────────────────

WoundAnalysisRepo  = Annotated[WoundAnalysisRepository,   Depends(get_wound_analysis_repository)]
WoundAnalysisSvc   = Annotated[WoundAnalysisService,      Depends(get_wound_analysis_service)]
ImageProcessingSvc = Annotated[ImageProcessingService,    Depends(get_image_processing_service)]
OrchestrationSvc   = Annotated[AnalysisOrchestrationService, Depends(get_analysis_orchestration_service)]
ModelRepo          = Annotated[ModelRepository,           Depends(get_model_repository)]
ModelSvc           = Annotated[ModelService,              Depends(get_model_service)]
ResponseMapperDep  = Annotated[ResponseMapper,            Depends(get_response_mapper)]
WoundAISvc         = Annotated[WoundAIService,            Depends(get_wound_ai_service)]
FileSvc            = Annotated[FileService,               Depends(get_file_service)]
FileValidatorDep   = Annotated[FileValidator,             Depends(get_file_validator)]
