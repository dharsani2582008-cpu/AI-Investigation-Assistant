"""
Relationship analysis service (Phase 4).

Builds relationships between entities that share a source CONTEXT —
the same record/row (tabular evidence), the same page (PDF), or the
same document (non-tabular JSON, which has no row/page concept).
Never connects entities from different contexts just because they
appear somewhere in the same file.

Uses the entities already produced by Phase 3 (services/entity_store.py,
services/entity_extraction.py) — this module does not re-extract or
re-parse evidence, and does not create a second entity system.
"""

import uuid
from collections import defaultdict

from services.entity_extraction import (
    PERSON, ORGANIZATION, LOCATION, EMAIL, PHONE, ACCOUNT, TRANSACTION_ID,
    normalize_entity_text,
)

# ---------------------------------------------------------------------------
# Supported relationship types.
#
# Keyed by (source_entity_type, target_entity_type) -> (relationship_type, confidence).
# Confidence is a heuristic label (not a statistical probability) reflecting
# how directly the entity types imply the relationship.
#
# Deliberately neutral naming (ASSOCIATED_WITH_*, not OWNS/CONTROLS) since a
# shared record only shows entities co-occurring in evidence, not ownership,
# identity, or intent.
# ---------------------------------------------------------------------------
RELATIONSHIP_RULES = {
    (PERSON, EMAIL): ("HAS_EMAIL", 0.9),
    (PERSON, PHONE): ("HAS_PHONE", 0.9),
    (PERSON, LOCATION): ("LOCATED_AT", 0.75),
    (PERSON, ORGANIZATION): ("ASSOCIATED_WITH_ORGANIZATION", 0.7),
    (PERSON, ACCOUNT): ("HAS_ACCOUNT", 0.75),
    (ACCOUNT, TRANSACTION_ID): ("INVOLVED_IN_TRANSACTION", 0.8),
    (PERSON, TRANSACTION_ID): ("ASSOCIATED_WITH_TRANSACTION", 0.65),
    (ORGANIZATION, EMAIL): ("HAS_EMAIL", 0.7),
    (ORGANIZATION, PHONE): ("HAS_PHONE", 0.7),
}

ALL_RELATIONSHIP_TYPES = sorted({rel_type for rel_type, _ in RELATIONSHIP_RULES.values()})


def _context_key(entity: dict) -> str:
    """
    The 'shared source context' an entity belongs to:
    - a specific row/record for tabular evidence
    - a specific page for PDF evidence
    - the whole document for non-tabular JSON (no row/page concept there)
    """
    if entity.get("record_number") is not None:
        return f"record:{entity['record_number']}"
    if entity.get("page_number") is not None:
        return f"page:{entity['page_number']}"
    return "document"


def _method_for_context(context_key: str) -> str:
    if context_key.startswith("record:"):
        return "shared_record"
    if context_key.startswith("page:"):
        return "shared_page"
    return "shared_document"


def _make_relationship(source: dict, target: dict, relationship_type: str, confidence: float, method: str) -> dict:
    return {
        "relationship_id": f"REL-{uuid.uuid4().hex[:10]}",
        "source_entity_id": source["entity_id"],
        "source_entity_text": source["entity_text"],
        "source_entity_type": source["entity_type"],
        "target_entity_id": target["entity_id"],
        "target_entity_text": target["entity_text"],
        "target_entity_type": target["entity_type"],
        "relationship_type": relationship_type,
        "evidence_id": source["evidence_id"],
        "source_filename": source["source_filename"],
        "record_number": source.get("record_number"),
        "page_number": source.get("page_number"),
        "method": method,
        "confidence": confidence,
    }


def _relationship_key(r: dict):
    """Stable key for duplicate prevention — see module docstring for scope
    (same evidence + same context + same entity pair + same relationship type)."""
    return (
        r["evidence_id"],
        r.get("record_number"),
        r.get("page_number"),
        r["source_entity_type"],
        normalize_entity_text(r["source_entity_text"], r["source_entity_type"]),
        r["target_entity_type"],
        normalize_entity_text(r["target_entity_text"], r["target_entity_type"]),
        r["relationship_type"],
    )


def _dedupe_relationships(relationships: list) -> list:
    seen = set()
    out = []
    for r in relationships:
        key = _relationship_key(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _generate_for_context_group(group: list) -> list:
    """group: entities that all share the same evidence_id + context_key."""
    context_key = _context_key(group[0])
    method = _method_for_context(context_key)

    relationships = []
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            a, b = group[i], group[j]
            if a["entity_id"] == b["entity_id"]:
                continue

            pair = (a["entity_type"], b["entity_type"])
            rev_pair = (b["entity_type"], a["entity_type"])

            if pair in RELATIONSHIP_RULES:
                source, target = a, b
            elif rev_pair in RELATIONSHIP_RULES:
                source, target = b, a
            else:
                # No justified relationship type for this entity-type pair —
                # do NOT invent one just because they co-occur.
                continue

            rel_type, confidence = RELATIONSHIP_RULES[(source["entity_type"], target["entity_type"])]
            relationships.append(_make_relationship(source, target, rel_type, confidence, method))

    return relationships


def generate_relationships(entities: list) -> list:
    """
    Groups the given entities by (evidence_id, shared context) and generates
    relationships within each group only. Entities from different evidence,
    different rows/records, or different PDF pages are never connected.

    Returns a de-duplicated list of relationship dicts. Safe to call with
    an empty list, a single entity, or entities with no compatible pairs —
    returns [] rather than raising.
    """
    if not entities or len(entities) < 2:
        return []

    grouped = defaultdict(list)
    for e in entities:
        grouped[(e["evidence_id"], _context_key(e))].append(e)

    relationships = []
    for group in grouped.values():
        if len(group) < 2:
            continue
        relationships.extend(_generate_for_context_group(group))

    return _dedupe_relationships(relationships)
