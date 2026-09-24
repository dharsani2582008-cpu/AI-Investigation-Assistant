"""
Lightweight JSON-backed store for generated relationships (Phase 4).

Mirrors services/entity_store.py: a single JSON file, no database
dependency yet. Tracks which evidence_ids have already had their
relationships generated, so restarting Streamlit or revisiting the
Relationships page never re-generates (and never duplicates)
relationships for evidence already processed.

Relationships from different evidence sources are stored as separate
records even if they describe the same entity pair + relationship
type — provenance is never collapsed away (see add_relationships).
"""

import json
import os
from typing import List

from utils.config import PROCESSED_DIR

INDEX_PATH = os.path.join(PROCESSED_DIR, "relationships_index.json")

_EMPTY = {"relationships": [], "processed_evidence_ids": []}


def _ensure_index_file():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    if not os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(_EMPTY, f)


def _load_raw() -> dict:
    _ensure_index_file()
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "relationships" not in data:
            return dict(_EMPTY)
        data.setdefault("processed_evidence_ids", [])
        return data
    except (json.JSONDecodeError, TypeError, ValueError):
        return dict(_EMPTY)


def _save_raw(data: dict):
    _ensure_index_file()
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_relationships() -> List[dict]:
    return _load_raw()["relationships"]


def already_processed(evidence_id: str) -> bool:
    return evidence_id in _load_raw()["processed_evidence_ids"]


def add_relationships(evidence_id: str, relationships: List[dict]):
    """
    Appends new relationships and marks evidence_id as processed, even
    if generation produced zero relationships — so we don't retry it
    forever. Relationships already carry their own evidence_id, so
    provenance from multiple evidence sources is preserved automatically
    (nothing here merges or overwrites relationships from other files).
    """
    data = _load_raw()
    data["relationships"].extend(relationships)
    if evidence_id not in data["processed_evidence_ids"]:
        data["processed_evidence_ids"].append(evidence_id)
    _save_raw(data)


def get_by_evidence(evidence_id: str) -> List[dict]:
    return [r for r in load_relationships() if r.get("evidence_id") == evidence_id]


def clear_all():
    """Used only for tests / explicit reset — never called from the UI automatically."""
    _save_raw(dict(_EMPTY))
