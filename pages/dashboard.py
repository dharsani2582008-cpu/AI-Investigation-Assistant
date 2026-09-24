import streamlit as st

from services.analytics import (
    get_entity_statistics,
    get_relationship_statistics,
    get_evidence_statistics,
)
from services.evidence_store import load_index
from services.entity_store import load_entities
from services.relationship_store import load_relationships
from services.pattern_detection import detect_patterns


def render():
    st.header("Investigation Dashboard")
    st.caption(
        "Overview of uploaded evidence, entities, relationships, and investigation patterns."
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

    # Calculate statistics
    evidence_stats = get_evidence_statistics(evidence)
    entity_stats = get_entity_statistics(entities)
    relationship_stats = get_relationship_statistics(relationships)

    # Detect evidence-based investigation indicators
    patterns = detect_patterns(entities, relationships)

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Evidence Files",
        evidence_stats["total_evidence"],
    )

    col2.metric(
        "Total Entities",
        entity_stats["total_entities"],
    )

    col3.metric(
        "Relationships",
        relationship_stats["total_relationships"],
    )

    col4.metric(
        "Detected Patterns",
        len(patterns),
    )

    st.divider()

    # Entity statistics
    st.subheader("Entity Overview")

    if entity_stats["entity_types"]:
        st.bar_chart(entity_stats["entity_types"])
    else:
        st.info("No entities available yet.")

    # Relationship statistics
    st.subheader("Relationship Overview")

    if relationship_stats["relationship_types"]:
        st.bar_chart(relationship_stats["relationship_types"])
    else:
        st.info("No relationships available yet.")

    # Detected investigation indicators
    st.subheader("Detected Investigation Indicators")

    if patterns:
        for pattern in patterns:
            st.write(
                f"**{pattern['type']}** — {pattern['description']}"
            )
    else:
        st.info(
            "No evidence-based investigation indicators detected."
        )

    st.divider()

    # Evidence sources
    st.subheader("Evidence Sources")

    if evidence_stats["sources"]:
        for source, count in evidence_stats["sources"].items():
            st.write(
                f"**{source}** — {count} evidence item(s)"
            )
    else:
        st.info("No evidence uploaded yet.")

    st.divider()

    st.caption(
        "Analytics are derived from stored evidence, extracted entities, "
        "and recorded relationships. Investigation indicators are descriptive "
        "and require investigator review; they do not determine guilt or wrongdoing."
    )