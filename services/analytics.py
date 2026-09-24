from collections import Counter


def _get_value(item, key, default="UNKNOWN"):
    """Read a field from either a dictionary or an object."""
    if isinstance(item, dict):
        return item.get(key, default)

    return getattr(item, key, default)


def get_entity_statistics(entities):
    """Return basic statistics about extracted entities."""
    total = len(entities)

    type_counts = Counter(
        _get_value(entity, "entity_type")
        for entity in entities
    )

    evidence_counts = Counter(
        _get_value(entity, "evidence_id")
        for entity in entities
    )

    return {
        "total_entities": total,
        "entity_types": dict(type_counts),
        "entities_by_evidence": dict(evidence_counts),
    }


def get_relationship_statistics(relationships):
    """Return basic statistics about relationships."""
    total = len(relationships)

    type_counts = Counter(
        _get_value(relationship, "relationship_type")
        for relationship in relationships
    )

    evidence_counts = Counter(
        _get_value(relationship, "evidence_id")
        for relationship in relationships
    )

    return {
        "total_relationships": total,
        "relationship_types": dict(type_counts),
        "relationships_by_evidence": dict(evidence_counts),
    }


def get_evidence_statistics(evidence):
    """Return basic statistics about uploaded evidence."""
    total = len(evidence)

    source_counts = Counter(
        _get_value(item, "original_filename")
        for item in evidence
    )

    return {
        "total_evidence": total,
        "sources": dict(source_counts),
    }