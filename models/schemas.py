"""
Data schemas for evidence metadata.

This stays a plain dataclass (not a DB model) for now — SQLite storage
is a later phase (Phase 9 priority list). `to_dict`/`from_dict` let us
persist metadata as JSON in data/processed/evidence_index.json without
committing to a database schema too early.
"""

import uuid
from dataclasses import dataclass, asdict
from datetime import datetime


def generate_evidence_id() -> str:
    """Short unique id, e.g. 'EV-3f9a2b1c'."""
    return f"EV-{uuid.uuid4().hex[:8]}"


@dataclass
class EvidenceMetadata:
    evidence_id: str
    original_filename: str
    file_type: str            # csv, xlsx, json, pdf
    upload_timestamp: str
    num_records: int = 0       # rows for tabular, pages for pdf, items for json
    status: str = "uploaded"   # uploaded, processed, processed_with_warnings, failed
    original_path: str = ""
    processed_path: str = ""
    error_message: str = ""

    @staticmethod
    def new(original_filename: str, file_type: str) -> "EvidenceMetadata":
        return EvidenceMetadata(
            evidence_id=generate_evidence_id(),
            original_filename=original_filename,
            file_type=file_type,
            upload_timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "EvidenceMetadata":
        return EvidenceMetadata(**data)
