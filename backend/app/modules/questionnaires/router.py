from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import io
import traceback
import logging

logger = logging.getLogger(__name__)

from app.core.database import get_session
from app.modules.questionnaires.service import QuestionnaireService
from app.modules.questionnaires.schemas import (
    QuestionnaireCreate, QuestionnaireUpdate, QuestionnaireResponse,
    QuestionCreate, QuestionUpdate, QuestionResponse,
    AnswerOptionCreate, AnswerOptionUpdate, AnswerOptionResponse
)
from app.modules.questionnaires import import_export_service as ie

router = APIRouter()

def get_service(session: AsyncSession = Depends(get_session)) -> QuestionnaireService:
    return QuestionnaireService(session)

# ─── IMPORTANT: ALL static routes MUST come before dynamic /{q_id} routes ────
# FastAPI matches routes in order; "coverage", "templates/...", "import/..." etc.
# must be registered before @router.get("/{q_id}") or they'll be shadowed.

# ─── List / Create ────────────────────────────────────────────────────────────

@router.get("/", response_model=List[QuestionnaireResponse])
async def get_all_questionnaires(service: QuestionnaireService = Depends(get_service)):
    return await service.get_all()

@router.post("/", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
async def create_questionnaire(
    data: QuestionnaireCreate,
    service: QuestionnaireService = Depends(get_service)
):
    return await service.create_questionnaire(data)

# ─── Coverage / Gaps (STATIC – must be before /{q_id}) ───────────────────────

@router.get("/coverage")
async def get_coverage(service: QuestionnaireService = Depends(get_service)):
    """Return coverage stats: which wound types have an active questionnaire."""
    return await service.get_coverage()

# ─── Template Downloads (STATIC – must be before /{q_id}) ────────────────────

@router.get("/templates/csv")
async def download_csv_template():
    """Download a sample CSV template for importing questions into an existing questionnaire."""
    csv_bytes = ie.generate_csv_template()
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="questionnaire_template.csv"'}
    )

@router.get("/templates/excel")
async def download_excel_template():
    """Download a sample Excel template for importing questions."""
    excel_bytes = ie.generate_excel_template()
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="questionnaire_template.xlsx"'}
    )

@router.get("/templates/full-csv")
async def download_full_csv_template():
    """Download a CSV template for importing full questionnaire(s)."""
    csv_bytes = ie.generate_full_questionnaire_csv_template()
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="full_questionnaire_template.csv"'}
    )

@router.get("/templates/full-excel")
async def download_full_excel_template():
    """Download an Excel template for importing full questionnaire(s)."""
    excel_bytes = ie.generate_full_questionnaire_excel_template()
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="full_questionnaire_template.xlsx"'}
    )

# ─── Import (STATIC – must be before /{q_id}) ────────────────────────────────

@router.post("/import/preview")
async def preview_import(file: UploadFile = File(...)):
    """Preview parsed rows from CSV/Excel (add questions to existing questionnaire)."""
    filename = (file.filename or "").lower()
    content = await file.read()

    if filename.endswith(".csv"):
        rows, errors = ie.parse_csv(content)
    elif filename.endswith((".xlsx", ".xls")):
        rows, errors = ie.parse_excel(content)
    else:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ CSV hoặc Excel")

    return {
        "total_rows": len(rows),
        "errors": errors,
        "preview": rows[:50]
    }

@router.post("/import/full/preview")
async def preview_full_import(file: UploadFile = File(...)):
    """Preview full questionnaire(s) from CSV/Excel before importing."""
    filename = (file.filename or "").lower()
    content = await file.read()

    if filename.endswith(".csv"):
        groups, errors = ie.parse_full_csv(content)
    elif filename.endswith((".xlsx", ".xls")):
        groups, errors = ie.parse_full_excel(content)
    else:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ CSV hoặc Excel")

    return {
        "total_questionnaires": len(groups),
        "errors": errors,
        "preview": [
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
    }

@router.post("/import/full")
async def import_full_questionnaire(
    file: UploadFile = File(...),
    auto_activate: bool = Query(False, description="Tự động kích hoạt bộ vừa import"),
    service: QuestionnaireService = Depends(get_service)
):
    """Import a single full questionnaire from CSV/Excel (first group only)."""
    filename = (file.filename or "").lower()
    content = await file.read()

    if filename.endswith(".csv"):
        groups, errors = ie.parse_full_csv(content)
    elif filename.endswith((".xlsx", ".xls")):
        groups, errors = ie.parse_full_excel(content)
    else:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ CSV hoặc Excel")

    if not groups:
        raise HTTPException(
            status_code=422,
            detail={"message": "Không có dữ liệu hợp lệ", "errors": errors}
        )

    q = await service.import_full_questionnaire(groups[0], auto_activate=auto_activate)
    return {
        "imported": 1,
        "questionnaire_id": str(q.questionnaire_id),
        "title": q.title,
        "wound_type": q.wound_type,
        "errors": errors
    }

@router.post("/import/bulk")
async def import_bulk_questionnaires(
    file: UploadFile = File(...),
    service: QuestionnaireService = Depends(get_service)
):
    """Import ALL questionnaires from a single CSV/Excel file."""
    filename = (file.filename or "").lower()
    content = await file.read()

    if filename.endswith(".csv"):
        groups, errors = ie.parse_full_csv(content)
    elif filename.endswith((".xlsx", ".xls")):
        groups, errors = ie.parse_full_excel(content)
    else:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ CSV hoặc Excel")

    if not groups:
        raise HTTPException(
            status_code=422,
            detail={"message": "Không có dữ liệu hợp lệ", "errors": errors}
        )

    results = await service.import_bulk_questionnaires(groups)
    return {
        "imported": len(results),
        "questionnaires": [
            {
                "questionnaire_id": str(q.questionnaire_id),
                "title": q.title,
                "wound_type": q.wound_type,
                "is_active": q.is_active,
            }
            for q in results
        ],
        "errors": errors
    }

# ─── Question & Answer static-prefix routes ───────────────────────────────────
# These must also be before /{q_id} to avoid shadowing

@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: UUID,
    data: QuestionUpdate,
    service: QuestionnaireService = Depends(get_service)
):
    return await service.update_question(question_id, data)

@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: UUID, service: QuestionnaireService = Depends(get_service)):
    await service.delete_question(question_id)

@router.post("/questions/{question_id}/answers", response_model=AnswerOptionResponse, status_code=status.HTTP_201_CREATED)
async def add_answer(
    question_id: UUID,
    data: AnswerOptionCreate,
    service: QuestionnaireService = Depends(get_service)
):
    return await service.add_answer(question_id, data)

@router.put("/answers/{answer_id}", response_model=AnswerOptionResponse)
async def update_answer(
    answer_id: UUID,
    data: AnswerOptionUpdate,
    service: QuestionnaireService = Depends(get_service)
):
    return await service.update_answer(answer_id, data)

@router.delete("/answers/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer(answer_id: UUID, service: QuestionnaireService = Depends(get_service)):
    await service.delete_answer(answer_id)

# ─── DYNAMIC routes /{q_id} (must come LAST) ─────────────────────────────────

@router.get("/{q_id}", response_model=QuestionnaireResponse)
async def get_questionnaire(q_id: UUID, service: QuestionnaireService = Depends(get_service)):
    return await service.get_by_id(q_id)

@router.put("/{q_id}", response_model=QuestionnaireResponse)
async def update_questionnaire(
    q_id: UUID,
    data: QuestionnaireUpdate,
    service: QuestionnaireService = Depends(get_service)
):
    return await service.update_questionnaire(q_id, data)

@router.delete("/{q_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_questionnaire(q_id: UUID, service: QuestionnaireService = Depends(get_service)):
    await service.delete_questionnaire(q_id)

@router.post("/{q_id}/activate", response_model=QuestionnaireResponse)
async def activate_questionnaire(
    q_id: UUID,
    service: QuestionnaireService = Depends(get_service)
):
    """Activate this questionnaire and deactivate all others with same wound_type."""
    return await service.activate_questionnaire(q_id)

@router.post("/{q_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_question(
    q_id: UUID,
    data: QuestionCreate,
    service: QuestionnaireService = Depends(get_service)
):
    return await service.add_question(q_id, data)

@router.post("/{q_id}/import", response_model=QuestionnaireResponse)
async def import_file(
    q_id: UUID,
    file: UploadFile = File(...),
    service: QuestionnaireService = Depends(get_service)
):
    """Import questions from CSV or Excel file into an existing questionnaire."""
    filename = (file.filename or "").lower()
    content = await file.read()

    if filename.endswith(".csv"):
        rows, errors = ie.parse_csv(content)
    elif filename.endswith((".xlsx", ".xls")):
        rows, errors = ie.parse_excel(content)
    else:
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ file CSV (.csv) hoặc Excel (.xlsx, .xls)"
        )

    if not rows and errors:
        raise HTTPException(status_code=422, detail={"parse_errors": errors})

    return await service.import_questions_from_data(q_id, rows)

@router.get("/{q_id}/export/docx")
async def export_docx(q_id: UUID, service: QuestionnaireService = Depends(get_service)):
    """Export questionnaire as Word document (.docx)."""
    q = await service.get_by_id(q_id)
    file_bytes = ie.export_to_docx(q)
    safe_title = "".join(c for c in q.title if c.isascii() and (c.isalnum() or c in " _-"))[:40].strip() or "export"
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.docx"'}
    )

@router.get("/{q_id}/export/pdf")
async def export_pdf(q_id: UUID, service: QuestionnaireService = Depends(get_service)):
    """Export questionnaire as PDF (generated by ReportLab)."""
    q = await service.get_by_id(q_id)
    file_bytes = ie.export_to_pdf(q)
    safe_title = "".join(c for c in q.title if c.isascii() and (c.isalnum() or c in " _-"))[:40].strip() or "export"
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'}
    )

@router.get("/{q_id}/export/csv")
async def export_csv(q_id: UUID, service: QuestionnaireService = Depends(get_service)):
    """Export questionnaire as CSV in full re-importable format."""
    try:
        q = await service.get_by_id(q_id)
        file_bytes = ie.export_to_csv(q)
        safe_title = "".join(c for c in q.title if c.isascii() and (c.isalnum() or c in " _-"))[:40].strip() or "export"
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.csv"'}
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("[EXPORT CSV] Unexpected error for q_id=%s: %s", q_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export CSV thất bại: {type(exc).__name__}: {exc}")


@router.get("/{q_id}/export/excel")
async def export_excel(q_id: UUID, service: QuestionnaireService = Depends(get_service)):
    """Export questionnaire as Excel (.xlsx) in full re-importable format."""
    try:
        q = await service.get_by_id(q_id)
        file_bytes = ie.export_to_excel(q)
        safe_title = "".join(c for c in q.title if c.isascii() and (c.isalnum() or c in " _-"))[:40].strip() or "export"
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.xlsx"'}
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("[EXPORT EXCEL] Unexpected error for q_id=%s: %s", q_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export Excel thất bại: {type(exc).__name__}: {exc}")

