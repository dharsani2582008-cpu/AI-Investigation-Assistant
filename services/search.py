"""Local evidence retrieval for the Phase 5 AI assistant.

Retrieves only information already stored by Phases 2-4. No web or external
search is performed and no new evidence is inferred.
"""
from __future__ import annotations

import re
from typing import Any

from services import entity_store, relationship_store, evidence_store


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z0-9_@.\-/]+", (text or "").lower()) if len(t) >= 2]


def _score_text(query_tokens: list[str], *values: Any) -> int:
    haystack = " ".join(str(v or "") for v in values).lower()
    return sum(2 if token in haystack else 0 for token in query_tokens)


def search_entities(query: str, limit: int = 20) -> list[dict]:
    tokens = _tokens(query)
    if not tokens:
        return []
    scored = []
    for entity in entity_store.load_entities():
        score = _score_text(tokens, entity.get("entity_text"), entity.get("normalized_text"), entity.get("entity_type"), entity.get("source_filename"))
        if score:
            scored.append((score, entity))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("entity_text", ""))))
    return [dict(item[1], _score=item[0]) for item in scored[:limit]]


def search_relationships(query: str, limit: int = 30) -> list[dict]:
    tokens = _tokens(query)
    if not tokens:
        return []
    scored = []
    for rel in relationship_store.load_relationships():
        score = _score_text(
            tokens,
            rel.get("source_entity_text"), rel.get("target_entity_text"),
            rel.get("source_entity_type"), rel.get("target_entity_type"),
            rel.get("relationship_type"), rel.get("evidence_id"), rel.get("source_filename"),
        )
        if score:
            scored.append((score, rel))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("relationship_id", ""))))
    return [dict(item[1], _score=item[0]) for item in scored[:limit]]


def search_evidence(query: str, limit: int = 20) -> list[dict]:
    tokens = _tokens(query)
    if not tokens:
        return []
    scored = []
    for entry in evidence_store.load_index():
        score = _score_text(tokens, entry.evidence_id, entry.original_filename, entry.file_type, entry.status)
        if score:
            scored.append((score, entry.to_dict()))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("evidence_id", ""))))
    return [dict(item[1], _score=item[0]) for item in scored[:limit]]


def retrieve_context(query: str, max_entities: int = 20, max_relationships: int = 30) -> dict:
    """Retrieve relevant local evidence and preserve provenance."""
    entities = search_entities(query, max_entities)
    relationships = search_relationships(query, max_relationships)

    # If a matched entity is found, also include relationships touching that
    # entity even when the relationship text itself did not match all tokens.
    entity_ids = {e.get("entity_id") for e in entities}
    if entity_ids:
        related = []
        for rel in relationship_store.load_relationships():
            if rel.get("source_entity_id") in entity_ids or rel.get("target_entity_id") in entity_ids:
                if rel not in relationships:
                    related.append(rel)
        relationships.extend(related[:max(0, max_relationships - len(relationships))])

    evidence_ids = {e.get("evidence_id") for e in entities} | {r.get("evidence_id") for r in relationships}
    evidence = [e.to_dict() for e in evidence_store.load_index() if e.evidence_id in evidence_ids]

    return {
        "query": query,
        "entities": entities,
        "relationships": relationships,
        "evidence": evidence,
        "has_results": bool(entities or relationships or evidence),
    }
