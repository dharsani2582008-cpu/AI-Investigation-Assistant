"""
Manual smoke tests for Phase 3 entity extraction.

Runnable script (no pytest, matching tests/test_ingestion.py style):

    python tests/test_entities.py

Covers: each entity type, source/evidence_id traceability, CSV/JSON/PDF
extraction, and duplicate prevention across two extraction runs.
"""

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import EvidenceMetadata          # noqa: E402
from services import entity_extraction as ee          # noqa: E402
from services import file_loader, preprocessing        # noqa: E402

TMP = tempfile.mkdtemp(prefix="entity_test_")
results = []


def check(name, condition):
    results.append((name, bool(condition)))
    print(("PASS" if condition else "FAIL"), "-", name)


def has_type(entities, entity_type, text_substring=None):
    for e in entities:
        if e["entity_type"] != entity_type:
            continue
        if text_substring is None or text_substring.lower() in e["entity_text"].lower():
            return True
    return False


spacy_ok, spacy_msg = ee.get_spacy_status()
print(f"[spaCy status] available={spacy_ok} — {spacy_msg}")
print()

# ---------------------------------------------------------------------
# 1-9: individual entity type extraction from free text
# ---------------------------------------------------------------------
sample_text = (
    "Arun Kumar works at ABC Corporation in Coimbatore. "
    "Contact him at arun.kumar@example.com or 9876543210. "
    "He last logged in from 192.168.1.10 and visited https://example.com/report. "
    "The meeting was on 2024-01-05 and transaction TXN1001 was recorded."
)
found = ee.extract_entities_from_text(sample_text)
found_types = {(e_text.lower(), e_type) for e_text, e_type, _ in found}

check("EMAIL extraction", has_type(
    [{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.EMAIL, "arun.kumar@example.com"
))
check("PHONE extraction", has_type(
    [{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.PHONE, "987"
))
check("URL extraction", has_type(
    [{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.URL, "example.com/report"
))
check("IP_ADDRESS extraction", has_type(
    [{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.IP_ADDRESS, "192.168.1.10"
))
check("TRANSACTION_ID extraction", has_type(
    [{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.TRANSACTION_ID, "TXN1001"
))
check("DATE extraction (regex or spaCy)", has_type(
    [{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.DATE
))

if spacy_ok:
    check("PERSON extraction (spaCy)", has_type(
        [{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.PERSON, "Arun Kumar"
    ))
    check("ORGANIZATION extraction (spaCy)", has_type(
        [{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.ORGANIZATION
    ))
    # Documented limitation: en_core_web_sm sometimes tags a place name as
    # ORG rather than GPE/LOCATION on short/ambiguous mentions. We test
    # loosely (LOCATION OR ORGANIZATION) and note this rather than assert
    # perfect NER, per the phase-3 instructions.
    loc_or_org = has_type([{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.LOCATION, "Coimbatore") \
        or has_type([{"entity_type": t, "entity_text": txt} for txt, t, _ in found], ee.ORGANIZATION, "Coimbatore")
    check("LOCATION extraction (spaCy, may be tagged ORG by small model — documented limitation)", loc_or_org)
else:
    print("SKIP - PERSON/ORGANIZATION/LOCATION checks (spaCy model not available)")

# ---------------------------------------------------------------------
# 11. CSV entity extraction + traceability (matches the phase-3 example)
# ---------------------------------------------------------------------
csv_path = os.path.join(TMP, "test_investigation_evidence.csv")
with open(csv_path, "w") as f:
    f.write("name,email,phone,location,transaction_id\n")
    f.write("Arun Kumar,arun.kumar@example.com,9876543210,Coimbatore,TXN1001\n")
    f.write("Jane Doe,jane.doe@example.com,9123456780,Chennai,TXN1002\n")

df, err = file_loader.load_csv(csv_path)
processed_df, _ = preprocessing.preprocess_dataframe(df)

evidence = EvidenceMetadata.new("test_investigation_evidence.csv", "csv")
evidence.status = "processed"
processed_json_path = os.path.join(TMP, f"{evidence.evidence_id}.json")
processed_df.to_json(processed_json_path, orient="records", indent=2)
evidence.processed_path = processed_json_path

csv_entities, csv_warning = ee.extract_entities_for_evidence(evidence)
check("CSV extraction produced entities", len(csv_entities) > 0)
check("CSV: EMAIL found", has_type(csv_entities, ee.EMAIL, "arun.kumar@example.com"))
check("CSV: PHONE found", has_type(csv_entities, ee.PHONE))
check("CSV: TRANSACTION_ID found", has_type(csv_entities, ee.TRANSACTION_ID, "TXN1001"))
if spacy_ok:
    check("CSV: PERSON found", has_type(csv_entities, ee.PERSON, "Arun Kumar"))

check(
    "Entity traceability: evidence_id + source_filename + record_number + source_column present",
    all(
        e.get("evidence_id") == evidence.evidence_id
        and e.get("source_filename") == "test_investigation_evidence.csv"
        and e.get("record_number") is not None
        and e.get("source_column") is not None
        for e in csv_entities
    ),
)

# ---------------------------------------------------------------------
# 12. JSON entity extraction (non-tabular, recursive)
# ---------------------------------------------------------------------
json_evidence = EvidenceMetadata.new("case_notes.json", "json")
json_evidence.status = "processed"
json_processed_path = os.path.join(TMP, f"{json_evidence.evidence_id}.json")
raw_json_data = {
    "case_id": "X-1",
    "officer_notes": "Suspect contacted via jane.doe@example.com from IP 10.0.0.5.",
}
with open(json_processed_path, "w") as f:
    json.dump(raw_json_data, f)
json_evidence.processed_path = json_processed_path

json_entities, json_warning = ee.extract_entities_for_evidence(json_evidence)
check("JSON extraction produced entities", len(json_entities) > 0)
check("JSON: EMAIL found", has_type(json_entities, ee.EMAIL, "jane.doe@example.com"))
check("JSON: IP_ADDRESS found", has_type(json_entities, ee.IP_ADDRESS, "10.0.0.5"))
check(
    "JSON traceability: evidence_id + JSON path in source_column",
    all(e.get("evidence_id") == json_evidence.evidence_id and e.get("source_column") for e in json_entities),
)

# ---------------------------------------------------------------------
# 13. PDF entity extraction
# ---------------------------------------------------------------------
try:
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

    pdf_path = os.path.join(TMP, "investigation_notes.pdf")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Contact: officer@example.gov, case opened 2024-02-10.")
    doc.save(pdf_path)
    doc.close()

    pages, pdf_err = file_loader.load_pdf(pdf_path)
    processed_pages, _ = preprocessing.preprocess_pdf_pages(pages)

    pdf_evidence = EvidenceMetadata.new("investigation_notes.pdf", "pdf")
    pdf_evidence.status = "processed"
    pdf_processed_path = os.path.join(TMP, f"{pdf_evidence.evidence_id}.json")
    with open(pdf_processed_path, "w") as f:
        json.dump(processed_pages, f)
    pdf_evidence.processed_path = pdf_processed_path

    pdf_entities, pdf_warning = ee.extract_entities_for_evidence(pdf_evidence)
    check("PDF extraction produced entities", len(pdf_entities) > 0)
    check("PDF: EMAIL found", has_type(pdf_entities, ee.EMAIL, "officer@example.gov"))
    check(
        "PDF traceability: evidence_id + page_number present",
        all(e.get("evidence_id") == pdf_evidence.evidence_id and e.get("page_number") == 1 for e in pdf_entities),
    )
except Exception as e:
    check(f"PDF entity test crashed unexpectedly: {e}", False)

# ---------------------------------------------------------------------
# 14. Duplicate prevention (entity_store level: re-running extraction for
# the same evidence_id should not add a second copy of its entities)
# ---------------------------------------------------------------------
sys.path.insert(0, TMP)
import utils.config as config_module  # noqa: E402

original_processed_dir = config_module.PROCESSED_DIR
config_module.PROCESSED_DIR = TMP
import importlib
from services import entity_store as es
importlib.reload(es)

es.clear_all()
es.add_entities(evidence.evidence_id, csv_entities)
count_after_first = len(es.load_entities())

# Simulate the page's "skip already-extracted evidence" logic.
if not es.already_extracted(evidence.evidence_id):
    es.add_entities(evidence.evidence_id, csv_entities)
count_after_second_attempt = len(es.load_entities())

check("Duplicate prevention: already_extracted() blocks re-adding", count_after_first == count_after_second_attempt)
check("already_extracted() reports True after first run", es.already_extracted(evidence.evidence_id))

config_module.PROCESSED_DIR = original_processed_dir

# ---------------------------------------------------------------------
shutil.rmtree(TMP, ignore_errors=True)

failed = [name for name, ok in results if not ok]
print()
print(f"{len(results) - len(failed)}/{len(results)} checks passed.")
if failed:
    print("FAILED:", failed)
    sys.exit(1)
