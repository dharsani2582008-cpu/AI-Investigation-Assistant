"""
Manual smoke tests for Phase 4 relationship analysis / knowledge graph.

Runnable script (matches tests/test_ingestion.py and tests/test_entities.py style):

    python tests/test_relationships.py

Covers: each required relationship type, evidence/record/page
traceability, duplicate prevention, storage + reload, NetworkX graph
construction, entity connection search, and that different rows /
different evidence files are never incorrectly connected.
"""

import json
import os
import shutil
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import relationship_analysis as ra   # noqa: E402
from services import graph_service as gs            # noqa: E402

TMP = tempfile.mkdtemp(prefix="relationship_test_")
results = []


def check(name, condition):
    results.append((name, bool(condition)))
    print(("PASS" if condition else "FAIL"), "-", name)


def make_entity(entity_type, text, evidence_id, source_filename,
                 record_number=None, page_number=None, source_column=None, method="regex"):
    """Builds a Phase-3-shaped entity dict without needing spaCy/file I/O."""
    return {
        "entity_id": f"ENT-{uuid.uuid4().hex[:10]}",
        "entity_text": text,
        "normalized_text": text.lower() if entity_type == "EMAIL" else text,
        "entity_type": entity_type,
        "evidence_id": evidence_id,
        "source_filename": source_filename,
        "record_number": record_number,
        "page_number": page_number,
        "source_column": source_column,
        "extraction_method": method,
        "confidence": 0.9,
    }


def rel_types(relationships):
    return {r["relationship_type"] for r in relationships}


def find_rel(relationships, rel_type, source_text=None, target_text=None):
    for r in relationships:
        if r["relationship_type"] != rel_type:
            continue
        if source_text and r["source_entity_text"] != source_text:
            continue
        if target_text and r["target_entity_text"] != target_text:
            continue
        return r
    return None


# ---------------------------------------------------------------------
# 1-4: required relationship types, generated from one CSV-style record
# (matches the phase-4 example: Arun Kumar / email / phone / location / txn)
# ---------------------------------------------------------------------
EV = "EV-test0001"
FNAME = "test_investigation_evidence.csv"

row1_entities = [
    make_entity("PERSON", "Arun Kumar", EV, FNAME, record_number=1, source_column="name", method="spacy"),
    make_entity("EMAIL", "arun.kumar@example.com", EV, FNAME, record_number=1, source_column="email"),
    make_entity("PHONE", "9876543210", EV, FNAME, record_number=1, source_column="phone"),
    make_entity("LOCATION", "Coimbatore", EV, FNAME, record_number=1, source_column="location", method="spacy"),
    make_entity("TRANSACTION_ID", "TXN1001", EV, FNAME, record_number=1, source_column="transaction_id"),
]
# A second, DIFFERENT record in the same evidence file — must NOT connect
# to row 1's entities.
row2_entities = [
    make_entity("PERSON", "Jane Doe", EV, FNAME, record_number=2, source_column="name", method="spacy"),
    make_entity("EMAIL", "jane.doe@example.com", EV, FNAME, record_number=2, source_column="email"),
]

all_entities = row1_entities + row2_entities
relationships = ra.generate_relationships(all_entities)

check("Person -> Email relationship (HAS_EMAIL)", find_rel(relationships, "HAS_EMAIL", "Arun Kumar", "arun.kumar@example.com") is not None)
check("Person -> Phone relationship (HAS_PHONE)", find_rel(relationships, "HAS_PHONE", "Arun Kumar", "9876543210") is not None)
check("Person -> Location relationship (LOCATED_AT)", find_rel(relationships, "LOCATED_AT", "Arun Kumar", "Coimbatore") is not None)
check("Person -> Transaction relationship (ASSOCIATED_WITH_TRANSACTION)", find_rel(relationships, "ASSOCIATED_WITH_TRANSACTION", "Arun Kumar", "TXN1001") is not None)

# ---------------------------------------------------------------------
# 5-6: evidence_id + record_number traceability
# ---------------------------------------------------------------------
arun_email_rel = find_rel(relationships, "HAS_EMAIL", "Arun Kumar", "arun.kumar@example.com")
check("Evidence ID traceability", arun_email_rel is not None and arun_email_rel["evidence_id"] == EV)
check("Record number traceability", arun_email_rel is not None and arun_email_rel["record_number"] == 1)
check("Source filename traceability", arun_email_rel is not None and arun_email_rel["source_filename"] == FNAME)

# ---------------------------------------------------------------------
# 7: PDF page traceability
# ---------------------------------------------------------------------
pdf_entities = [
    make_entity("PERSON", "Officer Smith", "EV-pdf01", "notes.pdf", page_number=3, method="spacy"),
    make_entity("EMAIL", "smith@example.gov", "EV-pdf01", "notes.pdf", page_number=3),
]
pdf_relationships = ra.generate_relationships(pdf_entities)
pdf_rel = find_rel(pdf_relationships, "HAS_EMAIL", "Officer Smith", "smith@example.gov")
check("PDF page traceability", pdf_rel is not None and pdf_rel["page_number"] == 3 and pdf_rel["method"] == "shared_page")

# ---------------------------------------------------------------------
# 14: different rows must NOT create relationships across each other
# ---------------------------------------------------------------------
cross_row_rel = find_rel(relationships, "HAS_EMAIL", "Arun Kumar", "jane.doe@example.com")
check("Different rows are NOT incorrectly connected", cross_row_rel is None)
check("Row 2 still gets its own valid relationship", find_rel(relationships, "HAS_EMAIL", "Jane Doe", "jane.doe@example.com") is not None)

# ---------------------------------------------------------------------
# Sanity: a lone entity (no compatible partner in context) produces nothing
# ---------------------------------------------------------------------
lone = [make_entity("DATE", "2024-01-05", "EV-lone", "f.csv", record_number=1)]
check("Single entity with no partner produces no relationships", ra.generate_relationships(lone) == [])
check("Empty entity list produces no relationships", ra.generate_relationships([]) == [])

# ---------------------------------------------------------------------
# 8, 9, 10: duplicate prevention + storage + reload after "restart"
# ---------------------------------------------------------------------
import importlib
import utils.config as config_module
config_module.PROCESSED_DIR = TMP
from services import relationship_store as rs
importlib.reload(rs)

rs.clear_all()
rs.add_relationships(EV, relationships)
count_after_first_store = len(rs.load_relationships())

# Simulate the page's guard: skip evidence already processed.
if not rs.already_processed(EV):
    rs.add_relationships(EV, relationships)
count_after_second_attempt = len(rs.load_relationships())
check("Duplicate prevention: already_processed() blocks re-adding", count_after_first_store == count_after_second_attempt)

# Simulate an app restart: reload the store fresh from disk.
importlib.reload(rs)
reloaded = rs.load_relationships()
check("Relationships reload after restart (persisted to disk)", len(reloaded) == count_after_first_store and len(reloaded) > 0)

# ---------------------------------------------------------------------
# 15: different evidence files must preserve separate provenance
# ---------------------------------------------------------------------
other_evidence_entities = [
    make_entity("PERSON", "Arun Kumar", "EV-other02", "other_file.csv", record_number=1, method="spacy"),
    make_entity("EMAIL", "arun.kumar@example.com", "EV-other02", "other_file.csv", record_number=1),
]
other_relationships = ra.generate_relationships(other_evidence_entities)
rs.add_relationships("EV-other02", other_relationships)
all_stored = rs.load_relationships()
arun_rels_by_evidence = {r["evidence_id"] for r in all_stored if r["source_entity_text"] == "Arun Kumar" and r["relationship_type"] == "HAS_EMAIL"}
check("Same entity pair from two evidence files keeps separate provenance", arun_rels_by_evidence == {EV, "EV-other02"})
check("Two evidence sources both contribute relationships (no overwrite)", len(all_stored) == count_after_first_store + len(other_relationships))

# ---------------------------------------------------------------------
# 11, 12: NetworkX node/edge creation
# ---------------------------------------------------------------------
G = gs.build_graph(all_stored)
check("NetworkX graph has nodes", G.number_of_nodes() > 0)
check("NetworkX graph has edges", G.number_of_edges() > 0)
check("NetworkX node attributes include entity_text/entity_type", all("entity_text" in data and "entity_type" in data for _, data in G.nodes(data=True)))
check("NetworkX edge attributes include relationship_type/evidence_id", all("relationship_type" in data and "evidence_id" in data for _, _, data in G.edges(data=True)))

# Graph with zero/one node should not crash.
G_empty = gs.build_graph([])
check("Graph with zero relationships has zero nodes and doesn't crash", G_empty.number_of_nodes() == 0)

# ---------------------------------------------------------------------
# 13: entity connection search
# ---------------------------------------------------------------------
matches = gs.find_entity_nodes(G, "Arun Kumar")
check("Entity connection search finds matching node(s)", len(matches) >= 1)
if matches:
    node_id = matches[0][0]
    connections = gs.get_connections(G, node_id)
    check("Entity connection search returns connections with relationship_type", all("relationship_type" in c for c in connections))
    check("Entity connection search connections include other entity text", all("other_entity_text" in c for c in connections))

no_match = gs.find_entity_nodes(G, "Nonexistent Person XYZ")
check("Entity connection search returns empty list for no match", no_match == [])

# ---------------------------------------------------------------------
shutil.rmtree(TMP, ignore_errors=True)

failed = [name for name, ok in results if not ok]
print()
print(f"{len(results) - len(failed)}/{len(results)} checks passed.")
if failed:
    print("FAILED:", failed)
    sys.exit(1)
