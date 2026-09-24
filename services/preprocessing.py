"""
Preprocessing service (Phase 2).

Operates only on the PARSED representation in memory — the original
uploaded file on disk in data/uploads/ is never modified. Every
function returns a report dict describing what was done, so the UI
can show it transparently instead of preprocessing being a "black box".
"""

import re
import pandas as pd


def _normalize_column_name(col: str) -> str:
    col = str(col).strip().lower()
    col = re.sub(r"[^\w]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")
    return col or "unnamed_column"


def preprocess_dataframe(df: pd.DataFrame):
    """
    Returns (processed_df, report). Never mutates the input df.
    """
    report = {
        "original_rows": len(df),
        "original_columns": len(df.columns),
        "missing_values_before": int(df.isna().sum().sum()),
    }

    processed = df.copy()

    # Normalize column names; keep a record of what changed.
    rename_map = {c: _normalize_column_name(c) for c in processed.columns}
    processed = processed.rename(columns=rename_map)
    report["renamed_columns"] = {k: v for k, v in rename_map.items() if k != v}

    # Strip whitespace on text columns.
    for col in processed.select_dtypes(include="object").columns:
        processed[col] = processed[col].apply(lambda v: v.strip() if isinstance(v, str) else v)

    # Treat now-empty strings as missing values for consistency.
    processed = processed.replace(r"^\s*$", pd.NA, regex=True)

    # Remove exact duplicate rows (evidence integrity: this only affects
    # the processed copy, never the original file).
    before = len(processed)
    processed = processed.drop_duplicates()
    report["duplicate_rows_removed"] = before - len(processed)

    # Best-effort date detection: only convert a column if its name hints
    # at a date/time AND most of its non-null values actually parse —
    # avoids corrupting unrelated columns that happen to contain numbers.
    date_columns_detected = []
    for col in processed.columns:
        if any(hint in col for hint in ("date", "time", "timestamp")):
            non_null_original = processed[col].notna().sum()
            if non_null_original == 0:
                continue
            converted = pd.to_datetime(processed[col], errors="coerce")
            non_null_converted = converted.notna().sum()
            if non_null_converted / non_null_original >= 0.6:
                processed[col] = converted
                date_columns_detected.append(col)

    report["date_columns_detected"] = date_columns_detected
    report["missing_values_after"] = int(processed.isna().sum().sum())
    report["processed_rows"] = len(processed)
    report["processed_columns"] = len(processed.columns)

    return processed, report


def preprocess_pdf_pages(pages: list):
    """
    Cleans whitespace in extracted PDF page text (does not alter page
    numbers or drop pages). Returns (processed_pages, report).
    """
    processed = []
    chars_before = 0
    chars_after = 0

    for p in pages:
        original_text = p.get("text", "") or ""
        chars_before += len(original_text)
        cleaned = re.sub(r"[ \t]+", " ", original_text)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = cleaned.strip()
        chars_after += len(cleaned)
        processed.append({"page": p["page"], "text": cleaned})

    report = {
        "pages": len(processed),
        "chars_before": chars_before,
        "chars_after": chars_after,
    }
    return processed, report


def preprocess_json_raw(data):
    """
    For JSON that couldn't be converted to a table: recursively strips
    whitespace from string values only. Structure (keys, list order,
    non-string types) is left untouched. Returns (processed_data, report).
    """
    strings_cleaned = {"count": 0}

    def _clean(node):
        if isinstance(node, str):
            cleaned = node.strip()
            if cleaned != node:
                strings_cleaned["count"] += 1
            return cleaned
        if isinstance(node, list):
            return [_clean(item) for item in node]
        if isinstance(node, dict):
            return {k: _clean(v) for k, v in node.items()}
        return node

    processed = _clean(data)
    report = {"strings_whitespace_cleaned": strings_cleaned["count"]}
    return processed, report
