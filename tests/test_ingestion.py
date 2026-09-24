"""
Manual smoke tests for Phase 2 ingestion/preprocessing services.

Not a pytest suite (kept dependency-free per project scope) — just a
runnable script with plain asserts. Run with:

    python tests/test_ingestion.py

It builds small sample files in a temp folder, runs them through
services/file_loader.py and services/preprocessing.py directly, and
prints PASS/FAIL for each case.
"""

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import file_loader, preprocessing  # noqa: E402

TMP = tempfile.mkdtemp(prefix="ingestion_test_")
results = []


def check(name, condition):
    results.append((name, bool(condition)))
    print(("PASS" if condition else "FAIL"), "-", name)


# ---------------------------------------------------------------------
# CSV — valid
# ---------------------------------------------------------------------
csv_path = os.path.join(TMP, "people.csv")
with open(csv_path, "w") as f:
    f.write("Full Name , Email ,Phone\n")
    f.write(" John Smith ,john@example.com,9876543210\n")
    f.write(" John Smith ,john@example.com,9876543210\n")  # duplicate row
    f.write("Jane Doe,jane@example.com,\n")

df, err = file_loader.load_csv(csv_path)
check("CSV loads without error", err == "" and df is not None)
check("CSV has 3 raw rows before preprocessing", len(df) == 3)

processed, report = preprocessing.preprocess_dataframe(df)
check("CSV duplicate row removed", report["duplicate_rows_removed"] == 1)
check("CSV columns normalized", list(processed.columns) == ["full_name", "email", "phone"])

# ---------------------------------------------------------------------
# CSV — empty (malformed case)
# ---------------------------------------------------------------------
empty_csv = os.path.join(TMP, "empty.csv")
open(empty_csv, "w").close()
df_empty, err_empty = file_loader.load_csv(empty_csv)
check("Empty CSV returns error, not a crash", df_empty is None and err_empty != "")

# ---------------------------------------------------------------------
# XLSX — valid
# ---------------------------------------------------------------------
try:
    import pandas as pd
    xlsx_path = os.path.join(TMP, "records.xlsx")
    pd.DataFrame({"Name": ["Alice", "Bob"], "Amount": [100, 200]}).to_excel(xlsx_path, index=False)
    df_xlsx, err_xlsx = file_loader.load_xlsx(xlsx_path)
    check("XLSX loads without error", err_xlsx == "" and df_xlsx is not None)
    check("XLSX has 2 rows", len(df_xlsx) == 2)
except Exception as e:
    check(f"XLSX test crashed unexpectedly: {e}", False)

# ---------------------------------------------------------------------
# JSON — list of records (tabular)
# ---------------------------------------------------------------------
json_list_path = os.path.join(TMP, "list.json")
with open(json_list_path, "w") as f:
    json.dump([{"name": "Alice", "amount": 5}, {"name": "Bob", "amount": 10}], f)
df_json, raw_json, err_json = file_loader.load_json(json_list_path)
check("JSON list-of-dicts becomes a table", df_json is not None and len(df_json) == 2)

# ---------------------------------------------------------------------
# JSON — malformed
# ---------------------------------------------------------------------
bad_json_path = os.path.join(TMP, "bad.json")
with open(bad_json_path, "w") as f:
    f.write("{not valid json,,,")
df_bad, raw_bad, err_bad = file_loader.load_json(bad_json_path)
check("Malformed JSON returns error, not a crash", df_bad is None and err_bad != "")

# ---------------------------------------------------------------------
# JSON — nested dict (non-tabular, falls back to raw)
# ---------------------------------------------------------------------
nested_json_path = os.path.join(TMP, "nested.json")
with open(nested_json_path, "w") as f:
    json.dump({"case": "X-1", "details": {"officer": "  Smith  "}}, f)
df_nested, raw_nested, err_nested = file_loader.load_json(nested_json_path)
check("Nested JSON falls back to raw structure", df_nested is None and raw_nested is not None)
processed_raw, raw_report = preprocessing.preprocess_json_raw(raw_nested)
check("Raw JSON whitespace cleaned", processed_raw["details"]["officer"] == "Smith")

# ---------------------------------------------------------------------
# PDF — valid (built with PyMuPDF itself)
# ---------------------------------------------------------------------
try:
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    pdf_path = os.path.join(TMP, "sample.pdf")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Investigation notes: John Smith met Jane Doe.")
    doc.save(pdf_path)
    doc.close()

    pages, pdf_err = file_loader.load_pdf(pdf_path)
    check("PDF text extracted", pages is not None and "John Smith" in pages[0]["text"])
    check("PDF page number preserved", pages[0]["page"] == 1)
except Exception as e:
    check(f"PDF test crashed unexpectedly: {e}", False)

# ---------------------------------------------------------------------
# PDF — invalid/corrupted file
# ---------------------------------------------------------------------
corrupt_pdf_path = os.path.join(TMP, "corrupt.pdf")
with open(corrupt_pdf_path, "wb") as f:
    f.write(b"not a real pdf")
pages_corrupt, err_corrupt = file_loader.load_pdf(corrupt_pdf_path)
check("Corrupted PDF returns error, not a crash", pages_corrupt is None and err_corrupt != "")

# ---------------------------------------------------------------------
shutil.rmtree(TMP, ignore_errors=True)

failed = [name for name, ok in results if not ok]
print()
print(f"{len(results) - len(failed)}/{len(results)} checks passed.")
if failed:
    print("FAILED:", failed)
    sys.exit(1)
