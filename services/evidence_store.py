"""
Lightweight JSON-backed metadata store for evidence.

A single index file (data/processed/evidence_index.json) is enough
for the MVP and keeps Phase 2 free of a database dependency. Phase 9
can swap this for SQLite without changing how pages/evidence.py calls
these functions, as long as the function signatures stay the same.
"""

import json
import os
from typing import List

from utils.config import PROCESSED_DIR
from models.schemas import EvidenceMetadata

INDEX_PATH = os.path.join(PROCESSED_DIR, "evidence_index.json")


def _ensure_index_file():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    if not os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_index() -> List[EvidenceMetadata]:
    _ensure_index_file()
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [EvidenceMetadata.from_dict(item) for item in raw]
    except (json.JSONDecodeError, TypeError, ValueError):
        # A corrupted index should not crash the app.
        return []


def save_index(entries: List[EvidenceMetadata]):
    _ensure_index_file()
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in entries], f, indent=2, default=str)


def add_entry(entry: EvidenceMetadata):
    entries = load_index()
    entries.append(entry)
    save_index(entries)


def get_entry(evidence_id: str):
    for e in load_index():
        if e.evidence_id == evidence_id:
            return e
    return None
