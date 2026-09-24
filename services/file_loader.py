"""
File loading/parsing for evidence ingestion (Phase 2).

Each loader is defensive: it never raises out to the caller. On
failure it returns None (or an empty result) plus a human-readable
error message so the UI can show it and move on to the next file
instead of crashing the whole app.

Return shapes:
- load_csv / load_xlsx  -> (DataFrame | None, error_message)
- load_json             -> (DataFrame | None, raw_data | None, error_message)
- load_pdf              -> (list[{"page": int, "text": str}] | None, warning_or_error)
    For PDFs, if pages are returned alongside a non-empty message, treat
    it as a WARNING (e.g. no extractable text) rather than a fatal error.
"""

import json
import pandas as pd


def load_csv(path: str):
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return None, "CSV file is empty or has no columns."
    except pd.errors.ParserError as e:
        return None, f"Could not parse CSV file: {e}"
    except Exception as e:
        return None, f"Unexpected error reading CSV: {e}"

    if df.empty:
        return None, "CSV file has no data rows."
    return df, ""


def load_xlsx(path: str):
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        return None, f"Could not parse Excel file: {e}"

    if df.empty:
        return None, "Excel file has no data rows."
    return df, ""


def load_json(path: str):
    """Returns (DataFrame | None, raw_data | None, error_message)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        return None, None, f"Malformed JSON: {e}"
    except UnicodeDecodeError:
        return None, None, "JSON file is not valid UTF-8 text."
    except Exception as e:
        return None, None, f"Could not read JSON file: {e}"

    try:
        # List of records -> straightforward table.
        if isinstance(raw, list):
            if not raw:
                return None, raw, "JSON file contains an empty list."
            if all(isinstance(item, dict) for item in raw):
                df = pd.json_normalize(raw)
                return df, raw, ""
            return None, raw, "JSON is a list but not a list of objects; showing raw structure only."

        # Dict of equal-length lists -> also tabular (e.g. column-oriented export).
        if isinstance(raw, dict):
            if raw and all(isinstance(v, list) for v in raw.values()):
                lengths = {len(v) for v in raw.values()}
                if len(lengths) == 1:
                    df = pd.DataFrame(raw)
                    return df, raw, ""
            return None, raw, "JSON structure is not directly tabular; showing raw structure only."

        return None, raw, "JSON root is not a list or object; showing raw structure only."
    except Exception as e:
        return None, raw, f"JSON loaded but could not be converted to a table: {e}"


def load_pdf(path: str):
    """Returns (list[{'page','text'}] | None, message). See module docstring for semantics."""
    try:
        import pymupdf as fitz  # PyMuPDF's current import name
    except ImportError:
        try:
            import fitz  # older PyMuPDF versions
        except ImportError:
            return None, "PyMuPDF is not installed. Run: pip install pymupdf"

    try:
        doc = fitz.open(path)
    except Exception as e:
        return None, f"Could not open PDF: {e}"

    if doc.page_count == 0:
        doc.close()
        return None, "PDF has no pages."

    pages = []
    try:
        for i, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            pages.append({"page": i, "text": text})
    except Exception as e:
        doc.close()
        return None, f"Could not extract text from PDF: {e}"
    finally:
        doc.close()

    if all(not p["text"] for p in pages):
        return pages, "No extractable text found (the PDF may be scanned/image-based)."

    return pages, ""
