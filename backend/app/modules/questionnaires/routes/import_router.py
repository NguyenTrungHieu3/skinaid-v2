from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import List
from uuid import UUID
import io
import logging

from app.shared.response import SuccessResponse
from app.modules.questionnaires.dependencies import QuestionnaireSvc
from app.modules.questionnaires.schemas.api import (
    QuestionnaireResponse,
    ImportPreviewResponse, FullImportPreviewResponse,
    SingleImportResponse, BulkImportResponse, BulkFilesImportResponse,
)
from app.modules.questionnaires.services import import_service as imp
from app.modules.questionnaires.exceptions import ImportValidationError

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/questionnaires")


# ─── Template Downloads ──────────────────────────────────────────────────────

@router.get(
    "/templates/csv",
    summary="Tải mẫu CSV (thêm câu hỏi)",
    description="Tải file CSV mẫu để import câu hỏi vào bộ câu hỏi đã có",
)
async def download_csv_template():
    csv_bytes = imp.generate_csv_template()
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="questionnaire_template.csv"'}
    )

@router.get(
    "/templates/excel",
    summary="Tải mẫu Excel (thêm câu hỏi)",
    description="Tải file Excel mẫu để import câu hỏi vào bộ câu hỏi đã có",
)
async def download_excel_template():
    excel_bytes = imp.generate_excel_template()
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="questionnaire_template.xlsx"'}
    )

@router.get(
    "/templates/full-csv",
    summary="Tải mẫu CSV (bộ câu hỏi đầy đủ)",
    description="Tải file CSV mẫu để import bộ câu hỏi hoàn chỉnh",
)
async def download_full_csv_template():
    csv_bytes = imp.generate_full_questionnaire_csv_template()
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="full_questionnaire_template.csv"'}
    )

@router.get(
    "/templates/full-excel",
    summary="Tải mẫu Excel (bộ câu hỏi đầy đủ)",
    description="Tải file Excel mẫu để import bộ câu hỏi hoàn chỉnh",
)
async def download_full_excel_template():
    excel_bytes = imp.generate_full_questionnaire_excel_template()
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="full_questionnaire_template.xlsx"'}
    )


# ─── Import Endpoints ────────────────────────────────────────────────────────

@router.post(
    "/import/preview",
    response_model=SuccessResponse[ImportPreviewResponse],
    summary="Preview import câu hỏi",
    description="Xem trước dữ liệu CSV/Excel trước khi import vào bộ câu hỏi đã có",
)
async def preview_import(file: UploadFile = File(...)):
    file_content = await file.read()
    try:
        rows, errors = imp.parse_file(file.filename, file_content)
    except ImportValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return SuccessResponse(
        message="Trích xuất xem trước thành công",
        data=ImportPreviewResponse(
            total_rows=len(rows),
            errors=errors,
            preview=rows[:50]
        )
    )

@router.post(
    "/import/full/preview",
    response_model=SuccessResponse[FullImportPreviewResponse],
    summary="Preview import bộ câu hỏi đầy đủ",
    description="Xem trước bộ câu hỏi từ CSV/Excel trước khi import",
)
async def preview_full_import(file: UploadFile = File(...)):
    file_content = await file.read()
    try:
        groups, errors = imp.parse_full_file(file.filename, file_content)
    except ImportValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return SuccessResponse(
        message="Trích xuất xem trước thành công",
        data=FullImportPreviewResponse(
            total_questionnaires=len(groups),
            errors=errors,
            preview=[
                {
                    "wound_type": g["wound_type"],
                    "title": g["title"],
                    "description": g.get("description", ""),
                    "is_active": g["is_active"],
                    "total_questions": len(g["questions"]),
                    "questions_preview": [
                        {
                            "order": q["order_index"],
                            "text": q["question_text"],
                            "answers_count": len(q["answers"]),
                        }
                        for q in g["questions"][:3]
                    ]
                }
                for g in groups
            ]
        )
    )

@router.post(
    "/import/full",
    response_model=SuccessResponse[SingleImportResponse],
    summary="Import bộ câu hỏi đầy đủ",
    description="Import bộ câu hỏi đầy đủ từ CSV/Excel (chỉ bộ đầu tiên trong file)",
)
async def import_full_questionnaire(
    file: UploadFile = File(...),
    auto_activate: bool = Query(False, description="Tự động kích hoạt bộ vừa import"),
    service: QuestionnaireSvc = None,
):
    file_content = await file.read()
    try:
        groups, errors = imp.parse_full_file(file.filename, file_content)
    except ImportValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    if not groups:
        raise HTTPException(
            status_code=422,
            detail={"message": "Không có dữ liệu hợp lệ", "errors": errors}
        )

    q = await service.import_full_questionnaire(groups[0], auto_activate=auto_activate)
    return SuccessResponse(
        message="Import bộ câu hỏi thành công",
        data=SingleImportResponse(
            imported=1,
            questionnaire_id=str(q.questionnaire_id),
            title=q.title,
            wound_type=q.wound_type,
            errors=errors
        )
    )

@router.post(
    "/import/bulk",
    response_model=SuccessResponse[BulkImportResponse],
    summary="Import nhiều bộ câu hỏi từ 1 file",
    description="Import tất cả bộ câu hỏi có trong 1 file CSV/Excel",
)
async def import_bulk_questionnaires(
    file: UploadFile = File(...),
    service: QuestionnaireSvc = None,
):
    file_content = await file.read()
    try:
        groups, errors = imp.parse_full_file(file.filename, file_content)
    except ImportValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    if not groups:
        raise HTTPException(
            status_code=422,
            detail={"message": "Không có dữ liệu hợp lệ", "errors": errors}
        )

    results = await service.import_bulk_questionnaires(groups)
    return SuccessResponse(
        message="Import nhiều bộ câu hỏi thành công",
        data=BulkImportResponse(
            imported=len(results),
            questionnaires=[
                {
                    "questionnaire_id": str(q.questionnaire_id),
                    "title": q.title,
                    "wound_type": q.wound_type,
                    "is_active": q.is_active,
                }
                for q in results
            ],
            errors=errors
        )
    )

@router.post(
    "/import/bulk-files",
    response_model=SuccessResponse[BulkFilesImportResponse],
    summary="Import từ nhiều file",
    description="Import nhiều file CSV/Excel cùng lúc — mỗi file tạo một hoặc nhiều bộ câu hỏi",
)
async def import_bulk_files(
    files: List[UploadFile] = File(...),
    auto_activate: bool = Query(False, description="Tự động kích hoạt bộ vừa import"),
    service: QuestionnaireSvc = None,
):
    if not files:
        raise HTTPException(status_code=400, detail="Không có file nào được gửi lên")

    # Read all file contents (HTTP concern), then delegate to service
    files_data = []
    for f in files:
        content = await f.read()
        files_data.append((f.filename, content))

    result = await service.import_bulk_files(files_data, auto_activate=auto_activate)

    if not result["imported"] and not result["questionnaires"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Không có dữ liệu hợp lệ từ bất kỳ file nào",
                "file_results": result["file_results"],
                "errors": result["errors"],
            }
        )

    return SuccessResponse(
        message="Import từ nhiều file thành công",
        data=BulkFilesImportResponse(
            imported=result["imported"],
            questionnaires=[
                {
                    "questionnaire_id": str(q.questionnaire_id),
                    "title": q.title,
                    "wound_type": q.wound_type,
                    "is_active": q.is_active,
                }
                for q in result["questionnaires"]
            ],
            file_results=result["file_results"],
            errors=result["errors"],
        )
    )


# ─── Dynamic import route /{q_id}/import ─────────────────────────────────────

@router.post(
    "/{q_id}/import",
    response_model=SuccessResponse[QuestionnaireResponse],
    summary="Import câu hỏi vào bộ đã có",
    description="Import câu hỏi từ CSV/Excel vào bộ câu hỏi đã tồn tại",
)
async def import_file(
    q_id: UUID,
    file: UploadFile = File(...),
    service: QuestionnaireSvc = None,
):
    file_content = await file.read()
    try:
        rows, errors = imp.parse_file(file.filename, file_content)
    except ImportValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    if not rows and errors:
        raise HTTPException(status_code=422, detail={"parse_errors": errors})

    result = await service.import_questions_from_data(q_id, rows)
    return SuccessResponse(
        message="Import câu hỏi thành công",
        data=result
    )
