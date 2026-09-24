"""
Entities page (Phase 3).

Automatically extracts entities from any evidence that hasn't been
processed yet (tracked in services/entity_store.py so restarts don't
re-extract), then shows a summary, a filterable table, and any
extraction warnings. Entity/relationship graph views are later phases.
"""

import streamlit as st
import pandas as pd

from services import evidence_store, entity_store, entity_extraction


def _run_extraction_for_new_evidence():
    """Extracts entities for any evidence not yet processed. Returns a
    list of (evidence, warning_message) for evidence that produced a
    warning, so the UI can surface them without stopping the page."""
    warnings = []
    all_evidence = evidence_store.load_index()
    pending = [e for e in all_evidence if not entity_store.already_extracted(e.evidence_id)]

    if not pending:
        return warnings

    with st.spinner(f"Extracting entities from {len(pending)} evidence item(s)..."):
        for evidence in pending:
            entities, warning = entity_extraction.extract_entities_for_evidence(evidence)
            entity_store.add_entities(evidence.evidence_id, entities)
            if warning:
                warnings.append((evidence, warning))
    return warnings


def render():
    st.header("Entities")
    st.caption(
        "Entities extracted from processed evidence using spaCy (PERSON, "
        "ORGANIZATION, LOCATION, DATE) and pattern matching (EMAIL, PHONE, "
        "URL, IP ADDRESS, TRANSACTION ID, ACCOUNT)."
    )

    spacy_ok, spacy_msg = entity_extraction.get_spacy_status()
    if not spacy_ok:
        st.warning(spacy_msg)

    if not evidence_store.load_index():
        st.info("No evidence has been uploaded yet. Go to **Evidence** to add files first.")
        return

    warnings = _run_extraction_for_new_evidence()
    if warnings:
        with st.expander(f"⚠️ {len(warnings)} evidence item(s) had extraction warnings", expanded=False):
            for evidence, msg in warnings:
                st.write(f"**{evidence.original_filename}** ({evidence.evidence_id}): {msg}")

    entities = entity_store.load_entities()
    if not entities:
        st.info("No entities have been extracted yet from the uploaded evidence.")
        return

    df = pd.DataFrame(entities)

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    st.subheader("Summary")
    counts = df["entity_type"].value_counts().to_dict()
    total = len(df)

    row1 = st.columns(6)
    row1[0].metric("Total Entities", total)
    for col, etype in zip(row1[1:], entity_extraction.ALL_TYPES[:5]):
        col.metric(etype.title(), counts.get(etype, 0))

    row2 = st.columns(6)
    for col, etype in zip(row2, entity_extraction.ALL_TYPES[5:]):
        col.metric(etype.replace("_", " ").title(), counts.get(etype, 0))

    st.divider()

    # ---------------------------------------------------------------
    # Filters
    # ---------------------------------------------------------------
    st.subheader("Entity Table")
    f1, f2, f3, f4 = st.columns(4)
    type_filter = f1.multiselect("Entity type", sorted(df["entity_type"].unique()))
    evidence_filter = f2.multiselect("Evidence ID", sorted(df["evidence_id"].unique()))
    file_filter = f3.multiselect("Source file", sorted(df["source_filename"].unique()))
    search_text = f4.text_input("Search text")

    filtered = df.copy()
    if type_filter:
        filtered = filtered[filtered["entity_type"].isin(type_filter)]
    if evidence_filter:
        filtered = filtered[filtered["evidence_id"].isin(evidence_filter)]
    if file_filter:
        filtered = filtered[filtered["source_filename"].isin(file_filter)]
    if search_text:
        filtered = filtered[filtered["entity_text"].str.contains(search_text, case=False, na=False)]

    display_cols = {
        "entity_text": "Entity",
        "entity_type": "Type",
        "evidence_id": "Evidence ID",
        "source_filename": "Source File",
        "record_number": "Record #",
        "page_number": "Page #",
        "source_column": "Source Column",
        "extraction_method": "Method",
        "confidence": "Confidence",
    }
    shown = filtered[list(display_cols.keys())].rename(columns=display_cols)
    st.dataframe(shown, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(shown)} of {total} total entities.")
