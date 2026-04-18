from fastapi import APIRouter, status, Depends
from typing import List, Any
from uuid import UUID

from app.shared.response import SuccessResponse
from app.modules.questionnaires.dependencies import QuestionnaireSvc
from app.core.dependencies import require_admin
from app.modules.users.models import User
from app.modules.audit.dependencies import AuditSvc
from app.modules.questionnaires.schemas.api import (
    QuestionnaireCreate, QuestionnaireUpdate, QuestionnaireResponse,
    QuestionCreate, QuestionUpdate, QuestionResponse,
    AnswerOptionCreate, AnswerOptionUpdate, AnswerOptionResponse,
    BulkDeleteRequest, BulkDeleteResponse,
)

router = APIRouter(prefix="/questionnaires")


# ─── List / Create ────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=SuccessResponse[List[QuestionnaireResponse]],
    summary="Lấy tất cả bộ câu hỏi",
    description="Trả về danh sách tất cả bộ câu hỏi kèm câu hỏi và đáp án",
)
async def get_all_questionnaires(service: QuestionnaireSvc):
    data = await service.get_all()
    return SuccessResponse(data=data)

@router.post(
    "/",
    response_model=SuccessResponse[QuestionnaireResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo bộ câu hỏi mới",
    description="Tạo bộ câu hỏi mới kèm câu hỏi và đáp án (nếu có)",
)
async def create_questionnaire(
    data: QuestionnaireCreate, 
    service: QuestionnaireSvc,
    audit_service: AuditSvc,
    current_user: User = Depends(require_admin),
):
    result = await service.create_questionnaire(data)
    await audit_service.log_event(
        action="create_questionnaire",
        user_id=current_user.user_id,
        resource_type="questionnaire",
        resource_id=str(result.id),
        details={"title": result.title, "wound_type": result.wound_type},
        success=True,
        description=f"Tạo bộ câu hỏi: {result.title}"
    )
    return SuccessResponse(
        message="Tạo bộ câu hỏi thành công",
        data=result
    )


# ─── Bulk Delete (STATIC – must be before /{q_id}) ───────────────────────────

@router.post(
    "/bulk-delete",
    response_model=SuccessResponse[BulkDeleteResponse],
    summary="Xóa nhiều bộ câu hỏi",
    description="Xóa hàng loạt bộ câu hỏi theo danh sách ID",
)
async def bulk_delete_questionnaires(
    body: BulkDeleteRequest,
    service: QuestionnaireSvc,
    audit_service: AuditSvc,
    current_user: User = Depends(require_admin),
):
    deleted = await service.bulk_delete_questionnaires(body.ids)
    await audit_service.log_event(
        action="bulk_delete_questionnaires",
        user_id=current_user.user_id,
        resource_type="questionnaire",
        details={"ids": [str(i) for i in body.ids], "deleted_count": deleted},
        success=True,
        description=f"Xóa hàng loạt {deleted} bộ câu hỏi"
    )
    return SuccessResponse(
        message=f"Đã xóa {deleted} bộ câu hỏi",
        data=BulkDeleteResponse(deleted=deleted, message=f"Đã xóa {deleted} bộ câu hỏi thành công")
    )


# ─── Coverage / Gaps (STATIC – must be before /{q_id}) ───────────────────────

@router.get(
    "/coverage",
    response_model=SuccessResponse[Any],
    summary="Thống kê phủ sóng bộ câu hỏi",
    description="Trả về thống kê bộ câu hỏi theo loại vết thương: đã có active hay chưa",
)
async def get_coverage(service: QuestionnaireSvc):
    data = await service.get_coverage()
    return SuccessResponse(data=data)


# ─── Question & Answer static-prefix routes ───────────────────────────────────
# These must also be before /{q_id} to avoid shadowing

@router.put(
    "/questions/{question_id}",
    response_model=SuccessResponse[QuestionResponse],
    summary="Cập nhật câu hỏi",
    description="Cập nhật nội dung, thứ tự hoặc trạng thái của câu hỏi",
)
async def update_question(question_id: UUID, data: QuestionUpdate, service: QuestionnaireSvc):
    result = await service.update_question(question_id, data)
    return SuccessResponse(
        message="Cập nhật câu hỏi thành công",
        data=result
    )

@router.delete(
    "/questions/{question_id}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[None],
    summary="Xóa câu hỏi",
    description="Xóa câu hỏi và tất cả đáp án liên quan",
)
async def delete_question(question_id: UUID, service: QuestionnaireSvc):
    await service.delete_question(question_id)
    return SuccessResponse(message="Xóa câu hỏi thành công")

@router.post(
    "/questions/{question_id}/answers",
    response_model=SuccessResponse[AnswerOptionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Thêm đáp án",
    description="Thêm đáp án mới cho câu hỏi",
)
async def add_answer(question_id: UUID, data: AnswerOptionCreate, service: QuestionnaireSvc):
    result = await service.add_answer(question_id, data)
    return SuccessResponse(
        message="Thêm đáp án thành công",
        data=result
    )

@router.put(
    "/answers/{answer_id}",
    response_model=SuccessResponse[AnswerOptionResponse],
    summary="Cập nhật đáp án",
    description="Cập nhật nội dung, mức triage hoặc thứ tự đáp án",
)
async def update_answer(answer_id: UUID, data: AnswerOptionUpdate, service: QuestionnaireSvc):
    result = await service.update_answer(answer_id, data)
    return SuccessResponse(
        message="Cập nhật đáp án thành công",
        data=result
    )

@router.delete(
    "/answers/{answer_id}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[None],
    summary="Xóa đáp án",
    description="Xóa đáp án khỏi câu hỏi",
)
async def delete_answer(answer_id: UUID, service: QuestionnaireSvc):
    await service.delete_answer(answer_id)
    return SuccessResponse(message="Xóa đáp án thành công")


# ─── DYNAMIC routes /{q_id} (must come LAST) ─────────────────────────────────

@router.get(
    "/{q_id}",
    response_model=SuccessResponse[QuestionnaireResponse],
    summary="Lấy chi tiết bộ câu hỏi",
    description="Trả về bộ câu hỏi kèm tất cả câu hỏi và đáp án",
)
async def get_questionnaire(q_id: UUID, service: QuestionnaireSvc):
    data = await service.get_by_id(q_id)
    return SuccessResponse(data=data)

@router.put(
    "/{q_id}",
    response_model=SuccessResponse[QuestionnaireResponse],
    summary="Cập nhật bộ câu hỏi",
    description="Cập nhật tiêu đề, mô tả hoặc trạng thái bộ câu hỏi",
)
async def update_questionnaire(
    q_id: UUID, 
    data: QuestionnaireUpdate, 
    service: QuestionnaireSvc,
    audit_service: AuditSvc,
    current_user: User = Depends(require_admin),
):
    result = await service.update_questionnaire(q_id, data)
    await audit_service.log_event(
        action="update_questionnaire",
        user_id=current_user.user_id,
        resource_type="questionnaire",
        resource_id=str(q_id),
        details={"title": result.title},
        success=True,
        description=f"Cập nhật bộ câu hỏi: {result.title}"
    )
    return SuccessResponse(
        message="Cập nhật bộ câu hỏi thành công",
        data=result
    )

@router.delete(
    "/{q_id}",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponse[None],
    summary="Xóa bộ câu hỏi",
    description="Xóa bộ câu hỏi kèm tất cả câu hỏi và đáp án",
)
async def delete_questionnaire(
    q_id: UUID, 
    service: QuestionnaireSvc,
    audit_service: AuditSvc,
    current_user: User = Depends(require_admin),
):
    await service.delete_questionnaire(q_id)
    await audit_service.log_event(
        action="delete_questionnaire",
        user_id=current_user.user_id,
        resource_type="questionnaire",
        resource_id=str(q_id),
        success=True,
        description=f"Xóa bộ câu hỏi ID: {q_id}"
    )
    return SuccessResponse(message="Xóa bộ câu hỏi thành công")

@router.post(
    "/{q_id}/activate",
    response_model=SuccessResponse[QuestionnaireResponse],
    summary="Kích hoạt bộ câu hỏi",
    description="Kích hoạt bộ câu hỏi này và tự động vô hiệu hóa các bộ khác có cùng wound_type",
)
async def activate_questionnaire(q_id: UUID, service: QuestionnaireSvc):
    result = await service.activate_questionnaire(q_id)
    return SuccessResponse(
        message="Kích hoạt bộ câu hỏi thành công",
        data=result
    )

@router.post(
    "/{q_id}/questions",
    response_model=SuccessResponse[QuestionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Thêm câu hỏi",
    description="Thêm câu hỏi mới kèm đáp án (nếu có) vào bộ câu hỏi",
)
async def add_question(q_id: UUID, data: QuestionCreate, service: QuestionnaireSvc):
    result = await service.add_question(q_id, data)
    return SuccessResponse(
        message="Thêm câu hỏi thành công",
        data=result
    )
