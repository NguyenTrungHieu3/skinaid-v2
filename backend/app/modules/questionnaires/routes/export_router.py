from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, Response
from uuid import UUID
import io
import logging

from app.modules.questionnaires.dependencies import QuestionnaireSvc
from app.modules.questionnaires.services import export_service as exp
from app.modules.questionnaires.exceptions import QuestionnaireNotFoundError

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/questionnaires")

VALID_EXPORT_FORMATS = ("csv", "excel", "docx", "pdf")


def _safe_filename(title: str) -> str:
    return "".join(c for c in title if c.isascii() and (c.isalnum() or c in " _-"))[:40].strip() or "export"


# ─── Bulk Export ──────────────────────────────────────────────────────────────

@router.post(
    "/export/bulk",
    summary="Export nhiều bộ câu hỏi",
    description="Export nhiều bộ câu hỏi đã chọn thành 1 file (CSV, Excel, DOCX hoặc PDF)",
)
async def export_bulk(body: dict, service: QuestionnaireSvc):
    ids = body.get("ids", [])
    fmt = body.get("format", "csv")

    if not ids:
        raise HTTPException(status_code=400, detail="Không có bộ câu hỏi nào được chọn")
    if fmt not in VALID_EXPORT_FORMATS:
        raise HTTPException(status_code=400, detail="Định dạng không hợp lệ. Hãy chọn 'csv', 'excel', 'docx' hoặc 'pdf'")

    try:
        file_bytes, filename, media_type = await service.export_bulk(ids, fmt)
    except QuestionnaireNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── Single Export (dynamic /{q_id}/export/...) ──────────────────────────────

@router.get(
    "/{q_id}/export/docx",
    summary="Export DOCX",
    description="Xuất bộ câu hỏi dưới dạng file Word (.docx)",
)
async def export_docx(q_id: UUID, service: QuestionnaireSvc):
    q = await service.get_by_id(q_id)
    file_bytes = exp.export_to_docx(q)
    safe_title = _safe_filename(q.title)
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.docx"'}
    )

@router.get(
    "/{q_id}/export/pdf",
    summary="Export PDF",
    description="Xuất bộ câu hỏi dưới dạng PDF với định dạng đẹp",
)
async def export_pdf(q_id: UUID, service: QuestionnaireSvc):
    q = await service.get_by_id(q_id)
    file_bytes = exp.export_to_pdf(q)
    safe_title = _safe_filename(q.title)
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'}
    )

@router.get(
    "/{q_id}/export/csv",
    summary="Export CSV",
    description="Xuất bộ câu hỏi dưới dạng CSV — có thể re-import lại vào hệ thống",
)
async def export_csv(q_id: UUID, service: QuestionnaireSvc):
    q = await service.get_by_id(q_id)
    file_bytes = exp.export_to_csv(q)
    safe_title = _safe_filename(q.title)
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.csv"'}
    )

@router.get(
    "/{q_id}/export/excel",
    summary="Export Excel",
    description="Xuất bộ câu hỏi dưới dạng Excel (.xlsx) — có thể re-import lại vào hệ thống",
)
async def export_excel(q_id: UUID, service: QuestionnaireSvc):
    q = await service.get_by_id(q_id)
    file_bytes = exp.export_to_excel(q)
    safe_title = _safe_filename(q.title)
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.xlsx"'}
    )
