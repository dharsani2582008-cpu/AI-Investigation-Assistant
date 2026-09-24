"""
Evidence page.

Phase 1 gave us: upload widget + basic validation.
Phase 2 adds: parsing (CSV/XLSX/JSON/PDF), preprocessing, evidence_id
generation, metadata tracking, and processed-data storage.

Each uploaded file is handled independently and wrapped in error
handling so one bad file never breaks the page for the others.
"""

import hashlib
import json
import os

import pandas as pd
import streamlit as st

from utils.config import UPLOADS_DIR, PROCESSED_DIR, ALLOWED_EXTENSIONS
from utils.helpers import (
    validate_uploaded_file,
    human_readable_size,
    get_extension,
    build_stored_filename,
)
from models.schemas import EvidenceMetadata
from services import evidence_store, file_loader, preprocessing


EXT_TO_TYPE = {".csv": "csv", ".xlsx": "xlsx", ".json": "json", ".pdf": "pdf"}


def _file_signature(uploaded_file) -> str:
    """Content hash so re-running the Streamlit script doesn't re-ingest
    (and re-append to the index) the same upload on every rerun."""
    return hashlib.md5(uploaded_file.getvalue()).hexdigest()


def _ingest_file(uploaded_file, file_type: str) -> dict:
    """
    Runs validation -> save original -> parse -> preprocess -> save
    processed -> build metadata, for a single file. Never raises;
    returns a result dict the UI renders. This is the only place that
    touches disk for a new upload.
    """
    result = {"preview_df": None, "preview_pages": None, "preview_raw": None, "report": None}

    metadata = EvidenceMetadata.new(uploaded_file.name, file_type)

    # 1. Save the original file untouched.
    stored_name = build_stored_filename(metadata.evidence_id, uploaded_file.name)
    original_path = os.path.join(UPLOADS_DIR, stored_name)
    try:
        with open(original_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        metadata.original_path = original_path
    except Exception as e:
        metadata.status = "failed"
        metadata.error_message = f"Could not save original file: {e}"
        result["metadata"] = metadata
        return result

    # 2. Parse based on type.
    try:
        if file_type == "csv":
            df, error = file_loader.load_csv(original_path)
            raw, pages = None, None
        elif file_type == "xlsx":
            df, error = file_loader.load_xlsx(original_path)
            raw, pages = None, None
        elif file_type == "json":
            df, raw, error = file_loader.load_json(original_path)
            pages = None
        elif file_type == "pdf":
            pages, error = file_loader.load_pdf(original_path)
            df, raw = None, None
        else:
            df, raw, pages, error = None, None, None, f"Unhandled file type: {file_type}"
    except Exception as e:
        # Defensive catch-all: a parser bug should not crash the app.
        metadata.status = "failed"
        metadata.error_message = f"Unexpected error while parsing: {e}"
        result["metadata"] = metadata
        return result

    # 3. PDF fatal-vs-warning: load_pdf returns pages=None only on fatal errors.
    if file_type == "pdf" and pages is None:
        metadata.status = "failed"
        metadata.error_message = error
        result["metadata"] = metadata
        return result

    # 4. Non-PDF fatal error (df is None and there's no raw structure to fall back on).
    if file_type in ("csv", "xlsx") and df is None:
        metadata.status = "failed"
        metadata.error_message = error
        result["metadata"] = metadata
        return result
    if file_type == "json" and df is None and raw is None:
        metadata.status = "failed"
        metadata.error_message = error
        result["metadata"] = metadata
        return result

    # 5. Preprocess + save processed representation.
    processed_path = os.path.join(PROCESSED_DIR, f"{metadata.evidence_id}.json")
    try:
        if file_type in ("csv", "xlsx"):
            processed_df, report = preprocessing.preprocess_dataframe(df)
            processed_df.to_json(processed_path, orient="records", date_format="iso", indent=2)
            metadata.num_records = len(processed_df)
            result["preview_df"] = processed_df
            result["report"] = report

        elif file_type == "json" and df is not None:
            processed_df, report = preprocessing.preprocess_dataframe(df)
            processed_df.to_json(processed_path, orient="records", date_format="iso", indent=2)
            metadata.num_records = len(processed_df)
            result["preview_df"] = processed_df
            result["report"] = report

        elif file_type == "json" and df is None:
            processed_raw, report = preprocessing.preprocess_json_raw(raw)
            with open(processed_path, "w", encoding="utf-8") as f:
                json.dump(processed_raw, f, indent=2, default=str)
            metadata.num_records = len(raw) if isinstance(raw, list) else 1
            result["preview_raw"] = processed_raw
            result["report"] = report

        elif file_type == "pdf":
            processed_pages, report = preprocessing.preprocess_pdf_pages(pages)
            with open(processed_path, "w", encoding="utf-8") as f:
                json.dump(processed_pages, f, indent=2)
            metadata.num_records = len(processed_pages)
            result["preview_pages"] = processed_pages
            result["report"] = report

        metadata.processed_path = processed_path
        # A non-fatal warning (e.g. PDF with no extractable text, or
        # JSON that couldn't be tabularized) still counts as processed,
        # just flagged so the investigator knows to double check it.
        metadata.status = "processed_with_warnings" if error else "processed"
        metadata.error_message = error or ""

    except Exception as e:
        metadata.status = "failed"
        metadata.error_message = f"Preprocessing failed: {e}"

    result["metadata"] = metadata
    return result


def _status_badge(status: str) -> str:
    return {
        "processed": "✅ Processed",
        "processed_with_warnings": "⚠️ Processed (with warnings)",
        "failed": "❌ Failed",
        "uploaded": "⬆️ Uploaded",
    }.get(status, status)


def _render_preview(result: dict, metadata: EvidenceMetadata):
    report = result.get("report")

    if result.get("preview_df") is not None:
        df = result["preview_df"]
        st.write(f"**Rows:** {len(df)}  |  **Columns:** {len(df.columns)}")
        st.dataframe(df.head(20), use_container_width=True)
    elif result.get("preview_pages") is not None:
        pages = result["preview_pages"]
        st.write(f"**Pages:** {len(pages)}")
        for p in pages[:3]:
            with st.container(border=True):
                st.caption(f"Page {p['page']}")
                text = p["text"] if p["text"] else "_(no extractable text on this page)_"
                st.text(text[:1000] + ("..." if len(text) > 1000 else ""))
        if len(pages) > 3:
            st.caption(f"...and {len(pages) - 3} more page(s).")
    elif result.get("preview_raw") is not None:
        st.write("Not directly tabular — showing raw structure preview:")
        st.json(result["preview_raw"] if isinstance(result["preview_raw"], (list, dict)) else {}, expanded=False)

    if report:
        with st.expander("Preprocessing report"):
            st.json(report)

    if metadata.error_message:
        if metadata.status == "failed":
            st.error(metadata.error_message)
        else:
            st.warning(metadata.error_message)


def render():
    st.header("Evidence Upload & Ingestion")
    st.caption(
        "Upload evidence files. Each file is validated, parsed, preprocessed, "
        "and tracked with a unique evidence ID. Original files are never modified."
    )

    if "ingest_cache" not in st.session_state:
        st.session_state.ingest_cache = {}  # signature -> result dict

    uploaded_files = st.file_uploader(
        "Upload evidence file(s)",
        type=[e.lstrip(".") for e in ALLOWED_EXTENSIONS],
        accept_multiple_files=True,
        help="You can upload CSV, Excel (.xlsx), JSON, or PDF files.",
    )

    if uploaded_files:
        st.subheader("Upload Results")
        for uploaded_file in uploaded_files:
            is_valid, message = validate_uploaded_file(uploaded_file)

            if not is_valid:
                with st.expander(f"📄 {uploaded_file.name}", expanded=True):
                    st.error(message)
                continue

            signature = _file_signature(uploaded_file)

            if signature not in st.session_state.ingest_cache:
                file_type = EXT_TO_TYPE[get_extension(uploaded_file.name)]
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    result = _ingest_file(uploaded_file, file_type)
                st.session_state.ingest_cache[signature] = result
                # Persist metadata only the first time we see this exact file.
                evidence_store.add_entry(result["metadata"])
            else:
                result = st.session_state.ingest_cache[signature]

            metadata = result["metadata"]
            with st.expander(f"📄 {metadata.original_filename} — {metadata.evidence_id}", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                c1.write(f"**Type:** {metadata.file_type.upper()}")
                c2.write(f"**Size:** {human_readable_size(getattr(uploaded_file, 'size', None))}")
                c3.write(f"**Records:** {metadata.num_records}")
                c4.write(f"**Status:** {_status_badge(metadata.status)}")
                st.caption(f"Uploaded: {metadata.upload_timestamp}")

                if metadata.status != "failed":
                    _render_preview(result, metadata)
                else:
                    st.error(metadata.error_message)

    st.divider()
    st.subheader("Evidence Library")
    entries = evidence_store.load_index()
    if not entries:
        st.write("No evidence processed yet.")
        return

    rows = [
        {
            "Evidence ID": e.evidence_id,
            "File Name": e.original_filename,
            "Type": e.file_type.upper(),
            "Records": e.num_records,
            "Status": _status_badge(e.status),
            "Uploaded": e.upload_timestamp,
        }
        for e in entries
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.caption(
        f"{len(entries)} evidence item(s) tracked. "
        "Full entity/relationship views are built in later phases."
    )
