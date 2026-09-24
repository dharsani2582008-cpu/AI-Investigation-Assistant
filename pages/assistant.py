"""Streamlit UI for the Phase 5 evidence-grounded AI assistant."""
import streamlit as st

from services import search, ai_assistant


def _source_rows(context: dict) -> list[dict]:
    rows = []
    seen = set()
    for e in context.get("entities", []):
        key = (e.get("evidence_id"), e.get("entity_id"))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "Evidence ID": e.get("evidence_id"),
            "Source": e.get("source_filename"),
            "Record/Page": e.get("record_number") or e.get("page_number") or "-",
            "Entity": e.get("entity_text"),
            "Type": e.get("entity_type"),
            "Relationship": "-",
        })
    for r in context.get("relationships", []):
        key = (r.get("evidence_id"), r.get("relationship_id"))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "Evidence ID": r.get("evidence_id"),
            "Source": r.get("source_filename"),
            "Record/Page": r.get("record_number") or r.get("page_number") or "-",
            "Entity": f"{r.get('source_entity_text')} → {r.get('target_entity_text')}",
            "Type": f"{r.get('source_entity_type')} → {r.get('target_entity_type')}",
            "Relationship": r.get("relationship_type"),
        })
    return rows


def render():
    st.header("AI Investigation Assistant")
    st.caption("Ask questions about uploaded evidence. Answers are grounded in locally stored evidence and relationships.")

    connected, status = ai_assistant.ollama_status()
    if connected and "not downloaded" not in status.lower():
        st.success(status)
    elif connected:
        st.warning(status)
    else:
        st.error(status)
        st.caption("The retrieval functions can still be tested, but an AI answer requires Ollama to be running.")

    question = st.text_area(
        "Ask a question about the evidence",
        placeholder="Example: Find all information associated with Arun Kumar",
        height=100,
    )

    c1, c2 = st.columns([1, 1])
    ask = c1.button("🔎 Ask AI", type="primary", use_container_width=True)
    clear = c2.button("Clear", use_container_width=True)

    if clear:
        st.session_state.pop("ai_answer", None)
        st.session_state.pop("ai_context", None)
        st.rerun()

    if ask:
        if not question.strip():
            st.warning("Enter a question first.")
            return

        with st.spinner("Searching local evidence..."):
            context = search.retrieve_context(question)

        if not context["has_results"]:
            st.info("No relevant evidence was found for this question.")
            return

        with st.spinner("Generating evidence-grounded answer..."):
            answer = ai_assistant.answer_question(question, context)

        st.session_state["ai_answer"] = answer
        st.session_state["ai_context"] = context

    if st.session_state.get("ai_answer"):
        st.subheader("AI Response")
        st.write(st.session_state["ai_answer"])

        context = st.session_state.get("ai_context", {})
        st.subheader("Evidence Sources")
        rows = _source_rows(context)
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No source records are available.")
