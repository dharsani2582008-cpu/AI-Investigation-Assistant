"""
Entity extraction service (Phase 3).

Hybrid approach:
- spaCy NER for PERSON, ORGANIZATION, LOCATION, DATE (unstructured text).
- Regex/rule-based extraction for EMAIL, PHONE, URL, IP_ADDRESS,
  TRANSACTION_ID (structured patterns).
- Column-name hints as a last-resort fallback for structured evidence
  where the value itself doesn't match a hard pattern (e.g. an account
  number with no obvious prefix) — never invents an entity type when
  there is no evidence for it.

This module has no Streamlit imports — it is called from
pages/entities.py but is independently testable (see tests/test_entities.py).
"""

import json
import re
import uuid
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Entity type constants
# ---------------------------------------------------------------------------
PERSON = "PERSON"
ORGANIZATION = "ORGANIZATION"
LOCATION = "LOCATION"
DATE = "DATE"
EMAIL = "EMAIL"
PHONE = "PHONE"
ACCOUNT = "ACCOUNT"
URL = "URL"
IP_ADDRESS = "IP_ADDRESS"
TRANSACTION_ID = "TRANSACTION_ID"

ALL_TYPES = [
    PERSON, ORGANIZATION, LOCATION, DATE, EMAIL, PHONE,
    ACCOUNT, URL, IP_ADDRESS, TRANSACTION_ID,
]

# ---------------------------------------------------------------------------
# Regex patterns (structured entities)
# ---------------------------------------------------------------------------
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_URL_RE = re.compile(r"\bhttps?://[^\s,;'\"<>]+|\bwww\.[^\s,;'\"<>]+", re.IGNORECASE)
_IP_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
)
# Digit sequence 7-15 digits long, allowing +, spaces, hyphens, parens as separators.
_PHONE_RE = re.compile(r"(?<!\w)\+?[\d][\d\-\.\s()]{5,16}\d(?!\w)")
# Alphanumeric transaction-style codes: a short letter prefix (often
# TXN/TX/TRANS) directly followed by digits, e.g. TXN1001, TX-1001.
_TXN_RE = re.compile(r"\b(?:TXN|TX|TRANS|TRN)[-_]?\d{3,}\b", re.IGNORECASE)
# Similar shape but for account-style prefixes.
_ACCOUNT_RE = re.compile(r"\b(?:ACC|ACCT|A\/C)[-_]?\d{3,}\b", re.IGNORECASE)
_DATE_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{1,2}-\d{1,2}-\d{2,4}\b"
)


def _valid_phone_digits(candidate: str) -> bool:
    digits = re.sub(r"\D", "", candidate)
    return 7 <= len(digits) <= 15


# ---------------------------------------------------------------------------
# Column-name hints (used only as a fallback when no regex/NER match found)
# ---------------------------------------------------------------------------
_COLUMN_HINTS = [
    (("email",), EMAIL),
    (("phone", "mobile", "contact_number", "tel"), PHONE),
    (("transaction", "txn"), TRANSACTION_ID),
    (("account", "acct"), ACCOUNT),
    (("url", "website", "link"), URL),
    (("ip_address", "ip"), IP_ADDRESS),
    (("location", "city", "place", "address"), LOCATION),
    (("organization", "organisation", "company", "org"), ORGANIZATION),
    (("date", "time", "timestamp"), DATE),
    (("name",), PERSON),
]


def _column_hint_type(column_name: str):
    if not column_name:
        return None
    col = column_name.lower()
    for keywords, entity_type in _COLUMN_HINTS:
        if any(k in col for k in keywords):
            return entity_type
    return None


# ---------------------------------------------------------------------------
# spaCy model — loaded lazily and cached; extraction degrades gracefully
# (regex-only) if spaCy or the language model isn't installed.
# ---------------------------------------------------------------------------
_SPACY_STATE = {"loaded": False, "nlp": None, "error": ""}

_SPACY_LABEL_MAP = {
    "PERSON": PERSON,
    "ORG": ORGANIZATION,
    "GPE": LOCATION,
    "LOC": LOCATION,
    "DATE": DATE,
}


def get_spacy_status():
    """Returns (available: bool, message: str). Triggers lazy load."""
    _load_spacy()
    if _SPACY_STATE["nlp"] is not None:
        return True, "spaCy model loaded (en_core_web_sm)."
    return False, _SPACY_STATE["error"]


def _load_spacy():
    if _SPACY_STATE["loaded"]:
        return
    _SPACY_STATE["loaded"] = True
    try:
        import spacy
    except ImportError:
        _SPACY_STATE["error"] = (
            "spaCy is not installed. PERSON/ORGANIZATION/LOCATION/DATE "
            "extraction will be skipped. Run: pip install spacy"
        )
        return
    try:
        _SPACY_STATE["nlp"] = spacy.load("en_core_web_sm")
    except OSError:
        _SPACY_STATE["error"] = (
            "spaCy language model 'en_core_web_sm' is not installed. "
            "PERSON/ORGANIZATION/LOCATION/DATE extraction will be skipped "
            "(structured entities like EMAIL/PHONE still work). "
            "Run: python -m spacy download en_core_web_sm"
        )
    except Exception as e:
        _SPACY_STATE["error"] = f"Could not load spaCy model: {e}"


def _spacy_extract(text: str):
    """Returns list of (matched_text, entity_type, method='spacy')."""
    _load_spacy()
    nlp = _SPACY_STATE["nlp"]
    if nlp is None or not text or not text.strip():
        return []
    try:
        doc = nlp(text)
    except Exception:
        return []
    out = []
    for ent in doc.ents:
        mapped = _SPACY_LABEL_MAP.get(ent.label_)
        if mapped:
            out.append((ent.text.strip(), mapped, "spacy"))
    return out


def _regex_extract(text: str):
    """Returns list of (matched_text, entity_type, method='regex')."""
    if not text:
        return []
    out = []
    for m in _EMAIL_RE.findall(text):
        out.append((m, EMAIL, "regex"))
    for m in _URL_RE.findall(text):
        out.append((m, URL, "regex"))
    for m in _IP_RE.findall(text):
        out.append((m, IP_ADDRESS, "regex"))
    for m in _TXN_RE.findall(text):
        out.append((m, TRANSACTION_ID, "regex"))
    for m in _ACCOUNT_RE.findall(text):
        out.append((m, ACCOUNT, "regex"))
    for m in _DATE_RE.findall(text):
        out.append((m, DATE, "regex"))
    for m in _PHONE_RE.findall(text):
        if _valid_phone_digits(m):
            out.append((m.strip(), PHONE, "regex"))
    return out


def normalize_entity_text(text: str, entity_type: str) -> str:
    """Light, non-destructive normalization. Original text is always
    kept separately for traceability — this is a display/matching aid."""
    text = re.sub(r"\s+", " ", text).strip()
    if entity_type == EMAIL:
        return text.lower()
    if entity_type == PERSON:
        # Title-case only when the text looks like ALL CAPS or all lower —
        # leave mixed-case names (already reasonably formatted) untouched.
        if text.isupper() or text.islower():
            return text.title()
        return text
    if entity_type in (TRANSACTION_ID, ACCOUNT):
        return text.upper()
    if entity_type == PHONE:
        return re.sub(r"[^\d+]", "", text)
    return text


def extract_entities_from_text(text: str, allow_ner: bool = True):
    """
    Runs regex + (optionally) spaCy NER on a single piece of text.
    Returns a de-duplicated list of (matched_text, entity_type, method).
    """
    if not text or not str(text).strip():
        return []
    text = str(text)
    found = _regex_extract(text)
    if allow_ner:
        found += _spacy_extract(text)

    seen = set()
    deduped = []
    for matched_text, entity_type, method in found:
        key = (entity_type, normalize_entity_text(matched_text, entity_type))
        if key in seen:
            continue
        seen.add(key)
        deduped.append((matched_text, entity_type, method))
    return deduped


def _make_entity(evidence, matched_text, entity_type, method, record_number=None,
                  page_number=None, source_column=None):
    normalized = normalize_entity_text(matched_text, entity_type)
    confidence = {"regex": 0.9, "spacy": 0.7, "column_hint": 0.6}.get(method, 0.5)
    return {
        "entity_id": f"ENT-{uuid.uuid4().hex[:10]}",
        "entity_text": matched_text.strip(),
        "normalized_text": normalized,
        "entity_type": entity_type,
        "evidence_id": evidence.evidence_id,
        "source_filename": evidence.original_filename,
        "record_number": record_number,
        "page_number": page_number,
        "source_column": source_column,
        "extraction_method": method,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Per-cell extraction (tabular evidence)
# ---------------------------------------------------------------------------
def _extract_cell(value, column_name, evidence, record_number):
    if value is None:
        return []
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none", "null", "nat"):
        return []

    hint_type = _column_hint_type(column_name)
    # Only let spaCy loose on columns that plausibly contain free text
    # (names/orgs/locations/unhinted) — avoids tagging codes/numbers as NER.
    allow_ner = hint_type in (None, PERSON, ORGANIZATION, LOCATION) and any(c.isalpha() for c in text)

    found = extract_entities_from_text(text, allow_ner=allow_ner)

    if not found and hint_type:
        # Fallback: trust the column's own label since no pattern matched
        # a value we otherwise have no basis to classify.
        found = [(text, hint_type, "column_hint")]

    return [
        _make_entity(evidence, matched_text, entity_type, method, record_number=record_number, source_column=column_name)
        for matched_text, entity_type, method in found
    ]


def extract_from_dataframe(df: pd.DataFrame, evidence):
    """Row-by-row, column-by-column extraction for tabular evidence."""
    entities = []
    for row_number, (_, row) in enumerate(df.iterrows(), start=1):
        for column_name, value in row.items():
            entities.extend(_extract_cell(value, str(column_name), evidence, row_number))
    return _dedupe_entities(entities)


# ---------------------------------------------------------------------------
# PDF page extraction
# ---------------------------------------------------------------------------
def extract_from_pdf_pages(pages: list, evidence):
    entities = []
    for p in pages:
        text = p.get("text", "")
        if not text:
            continue
        found = extract_entities_from_text(text, allow_ner=True)
        for matched_text, entity_type, method in found:
            entities.append(_make_entity(evidence, matched_text, entity_type, method, page_number=p.get("page")))
    return _dedupe_entities(entities)


# ---------------------------------------------------------------------------
# Non-tabular ("raw") JSON extraction — recursive walk over string leaves
# ---------------------------------------------------------------------------
def extract_from_raw_json(data, evidence):
    entities = []

    def _walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                _walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, item in enumerate(node):
                _walk(item, f"{path}[{i}]")
        elif isinstance(node, str):
            column_hint_column = path.split(".")[-1].split("[")[0] if path else None
            for e in _extract_cell(node, column_hint_column, evidence, record_number=None):
                e["source_column"] = path  # keep the full JSON path for traceability
                entities.append(e)

    _walk(data, "")
    return _dedupe_entities(entities)


def _dedupe_entities(entities: list) -> list:
    """
    Removes exact duplicates within one extraction run — same evidence,
    same location in the source, same type and normalized value.
    """
    seen = set()
    deduped = []
    for e in entities:
        key = (
            e["evidence_id"], e["entity_type"], e["normalized_text"],
            e.get("record_number"), e.get("page_number"), e.get("source_column"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)
    return deduped


# ---------------------------------------------------------------------------
# Top-level dispatcher: given Phase 2 evidence metadata, load its processed
# representation from disk and extract entities from it.
# ---------------------------------------------------------------------------
def extract_entities_for_evidence(evidence):
    """
    Returns (entities: list[dict], warning_message: str).
    `evidence` is an EvidenceMetadata instance from Phase 2.
    Never raises — failures are reported as a warning with 0 entities.
    """
    if evidence.status == "failed" or not evidence.processed_path:
        return [], "Evidence was not successfully processed in Phase 2; skipping extraction."

    try:
        with open(evidence.processed_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        return [], f"Could not read processed evidence file: {e}"

    try:
        if evidence.file_type == "pdf":
            if not isinstance(raw, list):
                return [], "Unexpected processed PDF structure; skipping extraction."
            if all(not p.get("text") for p in raw):
                return [], "PDF has no extractable text; nothing to extract entities from."
            return extract_from_pdf_pages(raw, evidence), ""

        if evidence.file_type in ("csv", "xlsx") or (evidence.file_type == "json" and isinstance(raw, list)):
            if not raw:
                return [], "No records found in processed evidence."
            df = pd.DataFrame(raw)
            return extract_from_dataframe(df, evidence), ""

        # Non-tabular JSON (dict or other structure).
        return extract_from_raw_json(raw, evidence), ""

    except Exception as e:
        return [], f"Entity extraction failed: {e}"
