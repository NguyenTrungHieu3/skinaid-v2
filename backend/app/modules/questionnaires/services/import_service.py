"""
Import Service for Questionnaire module.
- Import questions into existing questionnaire: CSV/Excel with (question_order, question_text, ...)
- Import NEW questionnaire(s) from CSV/Excel with (wound_type, title, description, is_active, question_order, ...)
"""
import io
import csv
import logging
from typing import List, Tuple, Dict
from collections import OrderedDict

from app.modules.questionnaires.exceptions import ImportValidationError

logger = logging.getLogger(__name__)

# Mapping Vietnamese → English for triage_level
TRIAGE_MAP = {
    "green": "green", "yellow": "yellow", "red": "red",
    "nhẹ": "green", "trung bình": "yellow", "nặng": "red",
    "vừa": "yellow",  # alias
}

# Mapping Vietnamese → English for wound_type
WOUND_TYPE_MAP = {
    "burn": "burn", "bỏng": "burn", "bỏng (burn)": "burn",
    "abrasion": "abrasion", "trầy xước": "abrasion", "trầy xước (abrasion)": "abrasion",
    "bruise": "bruise", "bầm tím": "bruise", "bầm tím (bruise)": "bruise",
    "fungal": "fungal", "nấm da": "fungal", "nấm da (fungal)": "fungal",
    "acne": "acne", "mụn trứng cá": "acne", "mụn trứng cá (acne)": "acne",
    "psoriasis": "psoriasis", "vảy nến": "psoriasis", "vảy nến (psoriasis)": "psoriasis",
    # (Removed previous extraneous types, but can keep mapping for safety if user imports an old file)
    "laceration": "laceration", "vết rách": "laceration", "vết rách (laceration)": "laceration",
    "rash": "rash", "phát ban": "rash", "phát ban (rash)": "rash",
    "normal": "normal", "bình thường": "normal", "bình thường (normal)": "normal",
    "cut": "cut", "vết cắt": "cut", "vết cắt (cut)": "cut",
}


# ─── File Dispatch (called by router — single entry point) ───────────────────

def parse_file(filename: str, content: bytes) -> Tuple[List[dict], List[str]]:
    """
    Parse an uploaded file (CSV or Excel) for adding questions to an existing questionnaire.
    Raises ImportValidationError if the file format is not supported.
    """
    name = (filename or "").lower()
    if name.endswith(".csv"):
        return parse_csv(content)
    elif name.endswith((".xlsx", ".xls")):
        return parse_excel(content)
    else:
        raise ImportValidationError("Chỉ hỗ trợ file CSV (.csv) hoặc Excel (.xlsx, .xls)")


def parse_full_file(filename: str, content: bytes) -> Tuple[List[dict], List[str]]:
    """
    Parse an uploaded file (CSV or Excel) for importing full questionnaire(s).
    Raises ImportValidationError if the file format is not supported.
    """
    name = (filename or "").lower()
    if name.endswith(".csv"):
        return parse_full_csv(content)
    elif name.endswith((".xlsx", ".xls")):
        return parse_full_excel(content)
    else:
        raise ImportValidationError("Chỉ hỗ trợ file CSV (.csv) hoặc Excel (.xlsx, .xls)")




# Columns for adding questions to EXISTING questionnaire
REQUIRED_COLUMNS = {"question_order", "question_text", "answer_text", "triage_level"}

# Columns for importing FULL questionnaire(s)
REQUIRED_FULL_COLUMNS = {"wound_type", "title", "question_order", "question_text", "answer_text", "triage_level"}

# Canonical wound types (must stay in sync with frontend WOUND_TYPES_FORM)
VALID_WOUND_TYPES = {
    "burn", "abrasion", "bruise", "cut", "fungal", "acne", "psoriasis"
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
        triage = TRIAGE_MAP.get(triage, None)
        if triage is None:
            errors.append(f"Dòng {i}: triage_level '{normalized.get('triage_level', '')}' không hợp lệ (nhẹ/trung bình/nặng)")
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
        triage = TRIAGE_MAP.get(triage, None)
        if triage is None:
            errors.append(f"Dòng {i}: triage_level '{normalized.get('triage_level', '')}' không hợp lệ")
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
    wound_type = WOUND_TYPE_MAP.get(wound_type, wound_type) # Fallback to original if not found
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
    triage = TRIAGE_MAP.get(triage, None)
    if triage is None:
        errors.append(f"Dòng {row_num}: triage_level '{n.get('triage_level', '')}' không hợp lệ")
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
