"""
Lightweight JSON-backed store for extracted entities (Phase 3).

Mirrors the pattern used by services/evidence_store.py in Phase 2:
a single JSON file, no database dependency yet. Tracks which
evidence_ids have already been run through extraction so restarting
Streamlit (or revisiting the Entities page) doesn't re-extract and
duplicate entities for evidence already processed.
"""

import json
import os
from typing import List

from utils.config import PROCESSED_DIR

INDEX_PATH = os.path.join(PROCESSED_DIR, "entities_index.json")

_EMPTY = {"entities": [], "extracted_evidence_ids": []}


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
        if not isinstance(data, dict) or "entities" not in data:
            return dict(_EMPTY)
        data.setdefault("extracted_evidence_ids", [])
        return data
    except (json.JSONDecodeError, TypeError, ValueError):
        return dict(_EMPTY)


def _save_raw(data: dict):
    _ensure_index_file()
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_entities() -> List[dict]:
    return _load_raw()["entities"]


def already_extracted(evidence_id: str) -> bool:
    return evidence_id in _load_raw()["extracted_evidence_ids"]


def add_entities(evidence_id: str, entities: List[dict]):
    """Appends new entities and marks evidence_id as extracted, even if
    the extraction produced zero entities — so we don't retry it forever."""
    data = _load_raw()
    data["entities"].extend(entities)
    if evidence_id not in data["extracted_evidence_ids"]:
        data["extracted_evidence_ids"].append(evidence_id)
    _save_raw(data)


def get_by_evidence(evidence_id: str) -> List[dict]:
    return [e for e in load_entities() if e.get("evidence_id") == evidence_id]


def clear_all():
    """Used only for tests / explicit reset — never called from the UI automatically."""
    _save_raw(dict(_EMPTY))
