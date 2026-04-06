"""
Test export CSV/Excel endpoints via HTTP.
Run: python test_export_api.py
"""
import requests
import sys

API_BASE = "http://localhost:8000/api/v1"

print("=" * 60)
print("EXPORT/IMPORT ENDPOINT TESTER")
print("=" * 60)

# Step 1: Get all questionnaires
print("\n[1] Fetching all questionnaires...")
try:
    r = requests.get(f"{API_BASE}/questionnaires/", timeout=10)
    print(f"    Status: {r.status_code}")
    if r.status_code != 200:
        print(f"    ERROR: {r.text[:500]}")
        sys.exit(1)
    qs = r.json()
    print(f"    Found {len(qs)} questionnaires")
    if not qs:
        print("    No questionnaires to test export. Exiting.")
        sys.exit(0)
    for q in qs:
        nq = len(q.get("questions", []))
        na = sum(len(qn.get("answers", [])) for qn in q.get("questions", []))
        print(f"    - [{q['questionnaire_id'][:8]}...] {q['title']} | wt={q['wound_type']} | active={q['is_active']} | questions={nq} | answers={na}")
except Exception as e:
    print(f"    CONNECTION ERROR: {e}")
    print("    Make sure the backend is running on http://localhost:8000")
    sys.exit(1)

# Use first questionnaire
q = qs[0]
q_id = q["questionnaire_id"]
print(f"\n[2] Testing exports for: {q['title']} (id={q_id})")

# Step 2: Test CSV export
print("\n[2a] Testing CSV export...")
try:
    r = requests.get(f"{API_BASE}/questionnaires/{q_id}/export/csv", timeout=30)
    print(f"    Status: {r.status_code}")
    print(f"    Headers: Content-Type={r.headers.get('content-type')}, Content-Disposition={r.headers.get('content-disposition')}")
    if r.status_code == 200:
        print(f"    Response size: {len(r.content)} bytes")
        csv_text = r.content.decode("utf-8-sig", errors="replace")
        lines = csv_text.strip().split("\n")
        print(f"    CSV lines: {len(lines)}")
        print(f"    Header: {lines[0][:200]}")
        if len(lines) > 1:
            print(f"    First data row: {lines[1][:200]}")
        # Save to file for inspection
        with open("test_export_result.csv", "w", encoding="utf-8-sig") as f:
            f.write(csv_text)
        print("    Saved to test_export_result.csv")
    else:
        print(f"    ERROR BODY: {r.text[:1000]}")
except Exception as e:
    print(f"    ERROR: {e}")
    import traceback; traceback.print_exc()

# Step 3: Test Excel export
print("\n[2b] Testing Excel export...")
try:
    r = requests.get(f"{API_BASE}/questionnaires/{q_id}/export/excel", timeout=30)
    print(f"    Status: {r.status_code}")
    print(f"    Headers: Content-Type={r.headers.get('content-type')}, Content-Disposition={r.headers.get('content-disposition')}")
    if r.status_code == 200:
        print(f"    Response size: {len(r.content)} bytes")
        with open("test_export_result.xlsx", "wb") as f:
            f.write(r.content)
        print("    Saved to test_export_result.xlsx")
        # Verify it's valid xlsx
        import openpyxl, io
        wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        print(f"    Excel rows: {len(rows)} (including header)")
        if rows:
            print(f"    Header: {rows[0]}")
        if len(rows) > 1:
            print(f"    First data row: {rows[1]}")
    else:
        print(f"    ERROR BODY: {r.text[:1000]}")
except Exception as e:
    print(f"    ERROR: {e}")
    import traceback; traceback.print_exc()

# Step 4: Test PDF export
print("\n[2c] Testing PDF export...")
try:
    r = requests.get(f"{API_BASE}/questionnaires/{q_id}/export/pdf", timeout=30)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        print(f"    Response size: {len(r.content)} bytes")
        print(f"    Looks like PDF: {r.content[:5]}")  # should start with %PDF
    else:
        print(f"    ERROR BODY: {r.text[:1000]}")
except Exception as e:
    print(f"    ERROR: {e}")

# Step 5: Test DOCX export
print("\n[2d] Testing DOCX export...")
try:
    r = requests.get(f"{API_BASE}/questionnaires/{q_id}/export/docx", timeout=30)
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        print(f"    Response size: {len(r.content)} bytes")
    else:
        print(f"    ERROR BODY: {r.text[:1000]}")
except Exception as e:
    print(f"    ERROR: {e}")

# Step 6: Test re-import of the CSV
print("\n[3] Testing re-import of exported CSV...")
try:
    csv_content = open("test_export_result.csv", "rb").read()
    r = requests.post(
        f"{API_BASE}/questionnaires/import/full/preview",
        files={"file": ("test_export_result.csv", csv_content, "text/csv")},
        timeout=30,
    )
    print(f"    Preview status: {r.status_code}")
    if r.status_code == 200:
        preview = r.json()
        print(f"    Total questionnaires parsed: {preview.get('total_questionnaires')}")
        print(f"    Errors: {preview.get('errors')}")
        for p in preview.get('preview', []):
            print(f"    - {p['wound_type']}: {p['title']} | questions={p['total_questions']}")
    else:
        print(f"    ERROR: {r.text[:1000]}")
except FileNotFoundError:
    print("    Skipped - CSV export file not available")
except Exception as e:
    print(f"    ERROR: {e}")

# Step 7: Test re-import of the Excel
print("\n[4] Testing re-import of exported Excel...")
try:
    xlsx_content = open("test_export_result.xlsx", "rb").read()
    r = requests.post(
        f"{API_BASE}/questionnaires/import/full/preview",
        files={"file": ("test_export_result.xlsx", xlsx_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        timeout=30,
    )
    print(f"    Preview status: {r.status_code}")
    if r.status_code == 200:
        preview = r.json()
        print(f"    Total questionnaires parsed: {preview.get('total_questionnaires')}")
        print(f"    Errors: {preview.get('errors')}")
        for p in preview.get('preview', []):
            print(f"    - {p['wound_type']}: {p['title']} | questions={p['total_questions']}")
    else:
        print(f"    ERROR: {r.text[:1000]}")
except FileNotFoundError:
    print("    Skipped - Excel export file not available")
except Exception as e:
    print(f"    ERROR: {e}")

# Step 8: Test template downloads
print("\n[5] Testing template downloads...")
for tpl_name, tpl_url in [
    ("CSV template", "/questionnaires/templates/csv"),
    ("Excel template", "/questionnaires/templates/excel"),
    ("Full CSV template", "/questionnaires/templates/full-csv"),
    ("Full Excel template", "/questionnaires/templates/full-excel"),
]:
    try:
        r = requests.get(f"{API_BASE}{tpl_url}", timeout=10)
        print(f"    {tpl_name}: status={r.status_code}, size={len(r.content)} bytes")
    except Exception as e:
        print(f"    {tpl_name}: ERROR - {e}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
