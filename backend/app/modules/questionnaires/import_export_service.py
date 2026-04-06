"""
Import/Export Service for Questionnaire module.
- Import questions into existing questionnaire: CSV/Excel with (question_order, question_text, ...)
- Import NEW questionnaire(s) from CSV/Excel with (wound_type, title, description, is_active, question_order, ...)
- Export: DOCX (.docx) / PDF (.pdf via reportlab) / CSV / Excel (re-importable full format)
"""
import io
import csv
import logging
from typing import List, Tuple, Dict
from collections import OrderedDict

logger = logging.getLogger(__name__)

from app.modules.questionnaires.models import Questionnaire, Question, AnswerOption


TRIAGE_COLORS = {
    "green":  (0.18, 0.80, 0.44),
    "yellow": (1.0, 0.80, 0.0),
    "red":    (0.9, 0.20, 0.20),
}
TRIAGE_LABELS = {"green": "Nhẹ", "yellow": "Vừa", "red": "Nặng"}

# Columns for adding questions to EXISTING questionnaire
REQUIRED_COLUMNS = {"question_order", "question_text", "answer_text", "triage_level"}

# Columns for importing FULL questionnaire(s)
REQUIRED_FULL_COLUMNS = {"wound_type", "title", "question_order", "question_text", "answer_text", "triage_level"}

# Canonical wound types (must stay in sync with frontend WOUND_TYPES_FORM)
VALID_WOUND_TYPES = {
    "burn", "abrasion", "bruise", "fungal", "laceration", "rash", "normal",
    "cut", "acne", "psoriasis"
}



# ─── CSV Parser ───────────────────────────────────────────────────────────────

def parse_csv(content: bytes) -> Tuple[List[dict], List[str]]:
    """
    Parse CSV bytes → list of row dicts.
    Returns (rows, errors).
    """
    errors: List[str] = []
    rows: List[dict] = []

    try:
        # Detect encoding
        text = content.decode("utf-8-sig")  # handles BOM
    except UnicodeDecodeError:
        try:
            text = content.decode("cp1252")
        except Exception:
            return [], ["Không thể đọc file. Hãy đảm bảo file được lưu dạng UTF-8."]

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return [], ["File CSV rỗng hoặc không có header."]

    actual_cols = {c.strip().lower() for c in reader.fieldnames}
    missing = REQUIRED_COLUMNS - actual_cols
    if missing:
        return [], [f"File thiếu các cột bắt buộc: {', '.join(missing)}"]

    for i, row in enumerate(reader, start=2):
        normalized = {k.strip().lower(): v.strip() for k, v in row.items()}
        triage = normalized.get("triage_level", "green").lower()
        if triage not in ("green", "yellow", "red"):
            errors.append(f"Dòng {i}: triage_level '{triage}' không hợp lệ (green/yellow/red)")
            triage = "green"

        try:
            order = int(normalized.get("question_order", 1))
        except ValueError:
            errors.append(f"Dòng {i}: question_order phải là số nguyên")
            order = i

        if not normalized.get("question_text", "").strip():
            errors.append(f"Dòng {i}: question_text rỗng, bỏ qua dòng này")
            continue

        normalized["question_order"] = order
        normalized["triage_level"] = triage
        rows.append(normalized)

    return rows, errors


# ─── Excel Parser ─────────────────────────────────────────────────────────────

def parse_excel(content: bytes) -> Tuple[List[dict], List[str]]:
    """
    Parse Excel (.xlsx/.xls) bytes → list of row dicts.
    Returns (rows, errors).
    """
    try:
        import openpyxl
    except ImportError:
        return [], ["Thư viện openpyxl chưa được cài. Chạy: pip install openpyxl"]

    errors: List[str] = []
    rows: List[dict] = []

    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
    except Exception as e:
        return [], [f"Không thể đọc file Excel: {str(e)}"]

    header_row = None
    data_rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            header_row = [str(c).strip().lower() if c else "" for c in row]
        else:
            data_rows.append(row)

    if not header_row:
        return [], ["File Excel rỗng hoặc không có header."]

    missing = REQUIRED_COLUMNS - set(header_row)
    if missing:
        return [], [f"File thiếu các cột bắt buộc: {', '.join(missing)}"]

    for i, row in enumerate(data_rows, start=2):
        normalized = {header_row[j]: str(v).strip() if v is not None else "" for j, v in enumerate(row) if j < len(header_row)}
        if not normalized.get("question_text", "").strip():
            continue

        triage = normalized.get("triage_level", "green").lower()
        if triage not in ("green", "yellow", "red"):
            errors.append(f"Dòng {i}: triage_level '{triage}' không hợp lệ, dùng 'green'")
            triage = "green"

        try:
            order = int(float(normalized.get("question_order", 1)))
        except (ValueError, TypeError):
            errors.append(f"Dòng {i}: question_order phải là số, dùng giá trị mặc định")
            order = i - 1

        normalized["question_order"] = order
        normalized["triage_level"] = triage
        rows.append(normalized)

    return rows, errors


# ─── DOCX Export ──────────────────────────────────────────────────────────────

def export_to_docx(questionnaire: Questionnaire) -> bytes:
    """Generate a Word (.docx) document for the questionnaire."""
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # Title
    title_para = doc.add_heading(questionnaire.title, level=1)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_para.runs[0]
    run.font.color.rgb = RGBColor(0x17, 0x80, 0x5f)

    # Meta info
    status_text = "✅ Đang hoạt động" if questionnaire.is_active else "📝 Bản nháp"
    meta = doc.add_paragraph()
    meta.add_run(f"Loại vết thương: ").bold = True
    meta.add_run(questionnaire.wound_type)
    meta.add_run("   |   ")
    meta.add_run(f"Trạng thái: ").bold = True
    meta.add_run(status_text)
    if questionnaire.description:
        desc = doc.add_paragraph()
        desc.add_run("Mô tả: ").bold = True
        desc.add_run(questionnaire.description)

    doc.add_paragraph()  # spacer

    questions = sorted(questionnaire.questions or [], key=lambda q: q.order_index)
    for idx, q in enumerate(questions, start=1):
        # Question heading
        q_para = doc.add_paragraph()
        run = q_para.add_run(f"Câu {idx}: {q.question_text}")
        run.bold = True
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0x0f, 0x17, 0x2a)

        mc_label = "(Chọn nhiều)" if q.is_multiple_choice else "(Chọn một)"
        q_para.add_run(f"  {mc_label}").italic = True

        # Answers table
        answers = sorted(q.answers or [], key=lambda a: a.order_index)
        if answers:
            table = doc.add_table(rows=1, cols=2)
            table.style = "Table Grid"
            hdr = table.rows[0].cells
            hdr[0].text = "Đáp án"
            hdr[1].text = "Mức độ Triage"

            for hdr_cell in hdr:
                for p in hdr_cell.paragraphs:
                    for r in p.runs:
                        r.bold = True

            for ans in answers:
                row = table.add_row().cells
                row[0].text = ans.answer_text
                triage_label = TRIAGE_LABELS.get(ans.triage_level, ans.triage_level)
                row[1].text = triage_label

        doc.add_paragraph()

    # Footer
    footer = doc.add_paragraph(f"Xuất bởi SkinAid Admin — {questionnaire.questionnaire_id}")
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.runs[0].font.size = Pt(8)
    footer.runs[0].font.color.rgb = RGBColor(0x94, 0xa3, 0xb8)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ─── PDF Export ───────────────────────────────────────────────────────────────

def export_to_pdf(questionnaire: Questionnaire) -> bytes:
    """Generate a PDF document for the questionnaire using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    PRIMARY = colors.HexColor("#17805f")
    LIGHT_GREEN = colors.HexColor("#dcfce7")
    LIGHT_YELLOW = colors.HexColor("#fef9c3")
    LIGHT_RED = colors.HexColor("#fee2e2")

    TRIAGE_BG = {"green": LIGHT_GREEN, "yellow": LIGHT_YELLOW, "red": LIGHT_RED}
    TRIAGE_FG = {
        "green":  colors.HexColor("#166534"),
        "yellow": colors.HexColor("#854d0e"),
        "red":    colors.HexColor("#991b1b"),
    }

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "Title", parent=styles["Title"],
        textColor=PRIMARY, fontSize=22, spaceAfter=6, alignment=TA_CENTER
    )
    style_meta = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#475569"), spaceAfter=4
    )
    style_question = ParagraphStyle(
        "Question", parent=styles["Normal"],
        fontSize=12, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12, spaceAfter=6
    )
    style_answer = ParagraphStyle(
        "Answer", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#334155")
    )

    story = []

    # Title
    story.append(Paragraph(questionnaire.title, style_title))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    story.append(Spacer(1, 0.3*cm))

    status_text = "✅ Đang hoạt động" if questionnaire.is_active else "📝 Bản nháp"
    story.append(Paragraph(
        f"<b>Loại vết thương:</b> {questionnaire.wound_type}   |   "
        f"<b>Trạng thái:</b> {status_text}",
        style_meta
    ))
    if questionnaire.description:
        story.append(Paragraph(f"<b>Mô tả:</b> {questionnaire.description}", style_meta))

    story.append(Spacer(1, 0.5*cm))

    questions = sorted(questionnaire.questions or [], key=lambda q: q.order_index)
    for idx, q in enumerate(questions, start=1):
        mc_label = "(Chọn nhiều)" if q.is_multiple_choice else "(Chọn một)"
        story.append(Paragraph(f"Câu {idx}: {q.question_text} <i>{mc_label}</i>", style_question))

        answers = sorted(q.answers or [], key=lambda a: a.order_index)
        if answers:
            table_data = [["Đáp án", "Mức độ Triage"]]
            for ans in answers:
                table_data.append([
                    Paragraph(ans.answer_text, style_answer),
                    Paragraph(TRIAGE_LABELS.get(ans.triage_level, ans.triage_level), style_answer)
                ])

            col_widths = [12*cm, 4*cm]
            t = Table(table_data, colWidths=col_widths)
            triage_style = [
                ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ROWBACKGROUND', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]
            # Color triage cells
            for row_i, ans in enumerate(answers, start=1):
                bg = TRIAGE_BG.get(ans.triage_level, colors.white)
                fg = TRIAGE_FG.get(ans.triage_level, colors.black)
                triage_style.append(('BACKGROUND', (1, row_i), (1, row_i), bg))
                triage_style.append(('TEXTCOLOR', (1, row_i), (1, row_i), fg))

            t.setStyle(TableStyle(triage_style))
            story.append(t)

        story.append(Spacer(1, 0.3*cm))

    # Footer
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER
    )
    story.append(Paragraph(f"Xuất bởi SkinAid Admin | ID: {questionnaire.questionnaire_id}", footer_style))

    doc.build(story)
    return buf.getvalue()


# ─── CSV / Excel Export (re-importable full format) ─────────────────────────

def export_to_csv(questionnaire: Questionnaire) -> bytes:
    """
    Export a questionnaire as a CSV in the full-import format
    (wound_type, title, description, is_active, question_order,
    question_text, is_multiple_choice, answer_text, triage_level).
    The resulting file can be re-imported via /import/full or /import/bulk.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "wound_type", "title", "description", "is_active",
        "question_order", "question_text", "is_multiple_choice",
        "answer_text", "triage_level"
    ])

    questions = sorted(questionnaire.questions or [], key=lambda q: q.order_index)
    if not questions:
        logger.warning(
            "[EXPORT CSV] Questionnaire '%s' has no questions loaded — "
            "exporting header-only file.",
            questionnaire.title,
        )

    for q in questions:
        answers = sorted(q.answers or [], key=lambda a: a.order_index)
        if answers:
            for ans in answers:
                writer.writerow([
                    questionnaire.wound_type,
                    questionnaire.title,
                    questionnaire.description or "",
                    str(questionnaire.is_active).lower(),
                    q.order_index,
                    q.question_text,
                    str(q.is_multiple_choice).lower(),
                    ans.answer_text,
                    ans.triage_level,
                ])
        else:
            writer.writerow([
                questionnaire.wound_type,
                questionnaire.title,
                questionnaire.description or "",
                str(questionnaire.is_active).lower(),
                q.order_index,
                q.question_text,
                str(q.is_multiple_choice).lower(),
                "",
                "green",
            ])

    return output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility


def export_to_excel(questionnaire: Questionnaire) -> bytes:
    """
    Export a questionnaire as an Excel (.xlsx) in the full-import format.
    The resulting file can be re-imported via /import/full or /import/bulk.
    """
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    questions = sorted(questionnaire.questions or [], key=lambda q: q.order_index)
    if not questions:
        logger.warning(
            "[EXPORT EXCEL] Questionnaire '%s' has no questions loaded — "
            "exporting header-only file.",
            questionnaire.title,
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bộ câu hỏi"

    headers = [
        "wound_type", "title", "description", "is_active",
        "question_order", "question_text", "is_multiple_choice",
        "answer_text", "triage_level"
    ]
    header_fill = PatternFill(fgColor="17805f", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # Triage color coding
    triage_fills = {
        "green":  PatternFill(fgColor="dcfce7", fill_type="solid"),
        "yellow": PatternFill(fgColor="fef9c3", fill_type="solid"),
        "red":    PatternFill(fgColor="fee2e2", fill_type="solid"),
    }

    for q in questions:
        answers = sorted(q.answers or [], key=lambda a: a.order_index)
        if answers:
            for ans in answers:
                row = [
                    questionnaire.wound_type,
                    questionnaire.title,
                    questionnaire.description or "",
                    str(questionnaire.is_active).lower(),
                    q.order_index,
                    q.question_text,
                    str(q.is_multiple_choice).lower(),
                    ans.answer_text,
                    ans.triage_level,   # raw enum: green/yellow/red
                ]
                ws.append(row)
                # Color the triage cell
                triage_cell = ws.cell(row=ws.max_row, column=9)
                triage_cell.fill = triage_fills.get(ans.triage_level, PatternFill())
        else:
            ws.append([
                questionnaire.wound_type,
                questionnaire.title,
                questionnaire.description or "",
                str(questionnaire.is_active).lower(),
                q.order_index,
                q.question_text,
                str(q.is_multiple_choice).lower(),
                "",
                "green",
            ])

    # Column widths
    col_widths = [12, 30, 30, 10, 14, 45, 18, 40, 12]
    for i, w in enumerate(col_widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # Add legend sheet
    ws2 = wb.create_sheet("Hướng dẫn")
    ws2.append(["Cột", "Mô tả", "Giá trị hợp lệ"])
    ws2.append(["wound_type", "Loại vết thương", "burn, abrasion, bruise, fungal, laceration, rash, normal, cut, acne, psoriasis"])
    ws2.append(["title", "Tiêu đề bộ câu hỏi", "Chuỗi văn bản"])
    ws2.append(["description", "Mô tả (tùy chọn)", "Chuỗi văn bản hoặc để trống"])
    ws2.append(["is_active", "Trạng thái kích hoạt", "true / false"])
    ws2.append(["question_order", "Số thứ tự câu hỏi", "Số nguyên (1, 2, 3...)"])
    ws2.append(["question_text", "Nội dung câu hỏi", "Chuỗi văn bản"])
    ws2.append(["is_multiple_choice", "Chọn nhiều đáp án", "true / false"])
    ws2.append(["answer_text", "Nội dung đáp án", "Chuỗi văn bản"])
    ws2.append(["triage_level", "Mức độ nghiêm trọng", "green / yellow / red"])
    ws2.append([])
    ws2.append(["Lưu ý:", "File này export từ hệ thống SkinAid và có thể re-import qua chức năng 'Import một bộ' hoặc 'Import nhiều bộ'"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─── Template CSV Download ────────────────────────────────────────────────────

def generate_csv_template() -> bytes:
    """Return a sample CSV template bytes for downloading."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["question_order", "question_text", "is_multiple_choice", "answer_text", "triage_level"])
    writer.writerow([1, "Diện tích vết bỏng của bạn?", "false", "Dưới 10cm²", "green"])
    writer.writerow([1, "Diện tích vết bỏng của bạn?", "false", "Từ 10-50cm²", "yellow"])
    writer.writerow([1, "Diện tích vết bỏng của bạn?", "false", "Trên 50cm²", "red"])
    writer.writerow([2, "Vị trí vết bỏng trên cơ thể?", "false", "Tay hoặc chân", "green"])
    writer.writerow([2, "Vị trí vết bỏng trên cơ thể?", "false", "Lưng hoặc ngực", "yellow"])
    writer.writerow([2, "Vị trí vết bỏng trên cơ thể?", "false", "Mặt hoặc vùng nhạy cảm", "red"])
    return output.getvalue().encode("utf-8-sig")  # BOM for Excel compatibility


def generate_excel_template() -> bytes:
    """Return a sample Excel template bytes for downloading."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Template"

    headers = ["question_order", "question_text", "is_multiple_choice", "answer_text", "triage_level"]
    header_fill = PatternFill(fgColor="17805f", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    sample_data = [
        [1, "Diện tích vết bỏng của bạn?", "false", "Dưới 10cm²", "green"],
        [1, "Diện tích vết bỏng của bạn?", "false", "Từ 10-50cm²", "yellow"],
        [1, "Diện tích vết bỏng của bạn?", "false", "Trên 50cm²", "red"],
        [2, "Vị trí vết bỏng trên cơ thể?", "false", "Tay hoặc chân", "green"],
        [2, "Vị trí vết bỏng trên cơ thể?", "false", "Lưng hoặc ngực", "yellow"],
    ]
    for row_data in sample_data:
        ws.append(row_data)

    # Column widths
    col_widths = [12, 45, 18, 40, 12]
    for i, w in enumerate(col_widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ─── Full Questionnaire Parsers ───────────────────────────────────────────────
# Format: wound_type | title | description | is_active | question_order |
#         question_text | is_multiple_choice | answer_text | triage_level
#
# Multiple questionnaires in one file → group by (wound_type, title)

def _normalize_row_full(raw: dict, row_num: int, errors: List[str]) -> dict | None:
    """Normalize a raw dict row for the full-questionnaire format."""
    n = {k.strip().lower(): str(v).strip() if v is not None else "" for k, v in raw.items()}

    wound_type = n.get("wound_type", "").strip().lower()
    if not wound_type:
        errors.append(f"Dòng {row_num}: wound_type rỗng, bỏ qua")
        return None

    title = n.get("title", "").strip()
    if not title:
        errors.append(f"Dòng {row_num}: title rỗng, bỏ qua")
        return None

    question_text = n.get("question_text", "").strip()
    if not question_text:
        return None  # silently skip blank question rows (separator rows)

    triage = n.get("triage_level", "green").strip().lower()
    if triage not in ("green", "yellow", "red"):
        errors.append(f"Dòng {row_num}: triage_level '{triage}' không hợp lệ → dùng 'green'")
        triage = "green"

    try:
        order = int(float(n.get("question_order", 1)))
    except (ValueError, TypeError):
        errors.append(f"Dòng {row_num}: question_order không hợp lệ → dùng 1")
        order = 1

    mc_val = n.get("is_multiple_choice", "false").strip().lower()
    is_mc = mc_val in ("true", "1", "yes")

    is_active_val = n.get("is_active", "false").strip().lower()
    is_active = is_active_val in ("true", "1", "yes")

    return {
        "wound_type": wound_type,
        "title": title,
        "description": n.get("description", "").strip(),
        "is_active": is_active,
        "question_order": order,
        "question_text": question_text,
        "is_multiple_choice": is_mc,
        "answer_text": n.get("answer_text", "").strip(),
        "triage_level": triage,
    }


def _group_rows_into_questionnaires(rows: List[dict]) -> List[dict]:
    """
    Group normalized rows into questionnaire structures.
    Key: (wound_type, title)  →  1 questionnaire dict
    Returns list[{wound_type, title, description, is_active, questions: [{...}]}]
    """
    groups: Dict[tuple, dict] = OrderedDict()

    for row in rows:
        key = (row["wound_type"], row["title"])
        if key not in groups:
            groups[key] = {
                "wound_type": row["wound_type"],
                "title": row["title"],
                "description": row["description"],
                "is_active": row["is_active"],
                "questions": OrderedDict(),   # question_order → {text, mc, answers[]}
            }

        q_order = row["question_order"]
        if q_order not in groups[key]["questions"]:
            groups[key]["questions"][q_order] = {
                "question_text": row["question_text"],
                "is_multiple_choice": row["is_multiple_choice"],
                "order_index": q_order,
                "answers": [],
            }

        answer_text = row.get("answer_text", "").strip()
        if answer_text:
            groups[key]["questions"][q_order]["answers"].append({
                "answer_text": answer_text,
                "triage_level": row["triage_level"],
            })

    result = []
    for g in groups.values():
        g["questions"] = list(g["questions"].values())
        result.append(g)
    return result


def parse_full_csv(content: bytes) -> Tuple[List[dict], List[str]]:
    """
    Parse a 'full questionnaire' CSV file.
    Returns (questionnaire_groups, errors).
    Each item in questionnaire_groups is ready to be saved as a Questionnaire.
    """
    errors: List[str] = []
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content.decode("cp1252")
        except Exception:
            return [], ["Không thể đọc file. Hãy lưu dạng UTF-8."]

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return [], ["File CSV rỗng hoặc không có header."]

    actual_cols = {c.strip().lower() for c in reader.fieldnames}
    missing = REQUIRED_FULL_COLUMNS - actual_cols
    if missing:
        return [], [f"File thiếu cột bắt buộc: {', '.join(sorted(missing))}"]

    rows = []
    for i, row in enumerate(reader, start=2):
        normalized = _normalize_row_full(row, i, errors)
        if normalized:
            rows.append(normalized)

    if not rows:
        return [], errors + ["Không có dữ liệu hợp lệ trong file."]

    return _group_rows_into_questionnaires(rows), errors


def parse_full_excel(content: bytes) -> Tuple[List[dict], List[str]]:
    """
    Parse a 'full questionnaire' Excel file.
    Returns (questionnaire_groups, errors).
    """
    try:
        import openpyxl
    except ImportError:
        return [], ["Thư viện openpyxl chưa được cài. Chạy: pip install openpyxl"]

    errors: List[str] = []

    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
    except Exception as e:
        return [], [f"Không thể đọc file Excel: {str(e)}"]

    header_row = None
    data_rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            header_row = [str(c).strip().lower() if c else "" for c in row]
        else:
            data_rows.append(row)

    if not header_row:
        return [], ["File Excel rỗng."]

    missing = REQUIRED_FULL_COLUMNS - set(header_row)
    if missing:
        return [], [f"File thiếu cột bắt buộc: {', '.join(sorted(missing))}"]

    rows = []
    for i, row_vals in enumerate(data_rows, start=2):
        raw = {header_row[j]: (row_vals[j] if j < len(row_vals) else None)
               for j in range(len(header_row))}
        normalized = _normalize_row_full(raw, i, errors)
        if normalized:
            rows.append(normalized)

    if not rows:
        return [], errors + ["Không có dữ liệu hợp lệ trong file."]

    return _group_rows_into_questionnaires(rows), errors


# ─── Full Questionnaire Templates ─────────────────────────────────────────────

def generate_full_questionnaire_csv_template() -> bytes:
    """Return a CSV template for importing full questionnaire(s)."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "wound_type", "title", "description", "is_active",
        "question_order", "question_text", "is_multiple_choice",
        "answer_text", "triage_level"
    ])
    # Sample: 1 questionnaire for "burn"
    sample = [
        ["burn", "Bộ đánh giá bỏng cơ bản", "Dùng để đánh giá mức độ bỏng", "true",
         1, "Diện tích vết bỏng của bạn?", "false", "Dưới 10cm²", "green"],
        ["burn", "Bộ đánh giá bỏng cơ bản", "Dùng để đánh giá mức độ bỏng", "true",
         1, "Diện tích vết bỏng của bạn?", "false", "Từ 10-50cm²", "yellow"],
        ["burn", "Bộ đánh giá bỏng cơ bản", "Dùng để đánh giá mức độ bỏng", "true",
         1, "Diện tích vết bỏng của bạn?", "false", "Trên 50cm²", "red"],
        ["burn", "Bộ đánh giá bỏng cơ bản", "Dùng để đánh giá mức độ bỏng", "true",
         2, "Vị trí vết bỏng?", "false", "Tay hoặc chân", "green"],
        ["burn", "Bộ đánh giá bỏng cơ bản", "Dùng để đánh giá mức độ bỏng", "true",
         2, "Vị trí vết bỏng?", "false", "Mặt hoặc vùng nhạy cảm", "red"],
        # Sample: 2nd questionnaire for "abrasion" (different wound_type+title = new questionnaire)
        ["abrasion", "Bộ trầy xước tiêu chuẩn", "", "true",
         1, "Độ sâu vết trầy?", "false", "Trầy nhẹ bề mặt", "green"],
        ["abrasion", "Bộ trầy xước tiêu chuẩn", "", "true",
         1, "Độ sâu vết trầy?", "false", "Chảy máu nhẹ", "yellow"],
        ["abrasion", "Bộ trầy xước tiêu chuẩn", "", "true",
         1, "Độ sâu vết trầy?", "false", "Chảy máu nhiều hoặc sâu", "red"],
    ]
    writer.writerows(sample)
    return output.getvalue().encode("utf-8-sig")


def generate_full_questionnaire_excel_template() -> bytes:
    """Return an Excel template for importing full questionnaire(s)."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bộ câu hỏi"

    headers = [
        "wound_type", "title", "description", "is_active",
        "question_order", "question_text", "is_multiple_choice",
        "answer_text", "triage_level"
    ]
    header_fill = PatternFill(fgColor="17805f", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")

    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    sample = [
        ["burn", "Bộ đánh giá bỏng cơ bản", "Đánh giá mức độ bỏng", "true",
         1, "Diện tích vết bỏng?", "false", "Dưới 10cm²", "green"],
        ["burn", "Bộ đánh giá bỏng cơ bản", "Đánh giá mức độ bỏng", "true",
         1, "Diện tích vết bỏng?", "false", "Từ 10-50cm²", "yellow"],
        ["burn", "Bộ đánh giá bỏng cơ bản", "Đánh giá mức độ bỏng", "true",
         1, "Diện tích vết bỏng?", "false", "Trên 50cm²", "red"],
        ["burn", "Bộ đánh giá bỏng cơ bản", "Đánh giá mức độ bỏng", "true",
         2, "Vị trí vết bỏng?", "false", "Tay hoặc chân", "green"],
        ["burn", "Bộ đánh giá bỏng cơ bản", "Đánh giá mức độ bỏng", "true",
         2, "Vị trí vết bỏng?", "false", "Mặt hoặc vùng nhạy cảm", "red"],
        ["abrasion", "Bộ trầy xước tiêu chuẩn", "", "true",
         1, "Độ sâu vết trầy?", "false", "Trầy nhẹ bề mặt", "green"],
        ["abrasion", "Bộ trầy xước tiêu chuẩn", "", "true",
         1, "Độ sâu vết trầy?", "false", "Chảy máu nhẹ", "yellow"],
    ]
    for row_data in sample:
        ws.append(row_data)

    col_widths = [12, 30, 30, 10, 14, 45, 18, 40, 12]
    for i, w in enumerate(col_widths, start=1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # Add a legend sheet
    ws2 = wb.create_sheet("Hướng dẫn")
    ws2.append(["Cột", "Mô tả", "Giá trị hợp lệ"])
    ws2.append(["wound_type", "Loại vết thương (bắt buộc)", "burn, abrasion, bruise, fungal, laceration, rash, normal"])
    ws2.append(["title", "Tiêu đề bộ câu hỏi (bắt buộc)", "Chuỗi văn bản"])
    ws2.append(["description", "Mô tả (tùy chọn)", "Chuỗi văn bản hoặc để trống"])
    ws2.append(["is_active", "Trạng thái kích hoạt", "true / false"])
    ws2.append(["question_order", "Số thứ tự câu hỏi (bắt buộc)", "Số nguyên (1, 2, 3...)"])
    ws2.append(["question_text", "Nội dung câu hỏi (bắt buộc)", "Chuỗi văn bản"])
    ws2.append(["is_multiple_choice", "Chọn nhiều đáp án", "true / false"])
    ws2.append(["answer_text", "Nội dung đáp án (bắt buộc)", "Chuỗi văn bản"])
    ws2.append(["triage_level", "Mức độ nghiêm trọng (bắt buộc)", "green / yellow / red"])
    ws2.append([])
    ws2.append(["Lưu ý:", "Nhiều bộ câu hỏi trong 1 file: dùng wound_type + title khác nhau"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

