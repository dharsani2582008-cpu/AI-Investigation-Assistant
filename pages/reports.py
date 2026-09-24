import json

import streamlit as st

from services.evidence_store import load_index
from services.entity_store import load_entities
from services.relationship_store import load_relationships
from services.pattern_detection import detect_patterns
from services.report_generator import (
    generate_report,
    generate_pdf,
)


def render():
    st.header("Investigation Reports")
    st.caption(
        "Generate a structured report from the stored investigation evidence."
    )

    # Load stored data
    try:
        evidence = load_index()
    except Exception:
        evidence = []

    try:
        entities = load_entities()
    except Exception:
        entities = []

    try:
        relationships = load_relationships()
    except Exception:
        relationships = []

    # Detect investigation indicators
    patterns = detect_patterns(entities, relationships)

    # Generate structured report
    report = generate_report(
        evidence,
        entities,
        relationships,
        patterns,
    )

    # Generate PDF
    pdf_data = generate_pdf(report)

    # Report summary
    st.subheader("Report Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Evidence Files",
        report["summary"]["evidence_files"],
    )

    col2.metric(
        "Entities",
        report["summary"]["total_entities"],
    )

    col3.metric(
        "Relationships",
        report["summary"]["total_relationships"],
    )

    col4.metric(
        "Indicators",
        report["summary"]["detected_patterns"],
    )

    st.divider()

    # Evidence sources
    st.subheader("Evidence Sources")

    if report["evidence"]:
        for item in report["evidence"]:
            filename = item.get(
                "original_filename",
                "Unknown source",
            )

            evidence_id = item.get(
                "evidence_id",
                "Unknown ID",
            )

            st.write(
                f"**{filename}** — Evidence ID: `{evidence_id}`"
            )
    else:
        st.info("No evidence available.")

    # Entities
    st.subheader("Extracted Entities")

    if report["entities"]:
        st.dataframe(
            report["entities"],
            use_container_width=True,
        )
    else:
        st.info("No entities available.")

    # Relationships
    st.subheader("Relationships")

    if report["relationships"]:
        st.dataframe(
            report["relationships"],
            use_container_width=True,
        )
    else:
        st.info("No relationships available.")

    # Investigation indicators
    st.subheader("Investigation Indicators")

    if report["patterns"]:
        for pattern in report["patterns"]:
            st.write(
                f"**{pattern['type']}** — "
                f"{pattern['description']}"
            )
    else:
        st.info(
            "No evidence-based investigation indicators detected."
        )

    st.divider()

    # Download section
    st.subheader("Download Report")

    report_json = json.dumps(
        report,
        indent=4,
        default=str,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="Download JSON Report",
            data=report_json,
            file_name="investigation_report.json",
            mime="application/json",
        )

    with col2:
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name="investigation_report.pdf",
            mime="application/pdf",
        )

    st.divider()

    st.caption(
        "This report summarizes stored evidence and derived relationships. "
        "Investigation indicators are descriptive and require investigator "
        "review; they do not determine guilt or wrongdoing."
    )