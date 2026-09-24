from collections import Counter


def detect_patterns(entities, relationships):
    """Detect basic evidence-based investigation indicators."""

    patterns = []

    # Count connections for each entity
    relationship_counts = Counter()

    for relationship in relationships:
        source = relationship.get("source_entity_text")
        target = relationship.get("target_entity_text")

        if source:
            relationship_counts[source] += 1

        if target:
            relationship_counts[target] += 1

    # Indicator 1: High connection count
    for entity, count in relationship_counts.items():
        if count >= 3:
            patterns.append({
                "type": "HIGH_CONNECTION_COUNT",
                "entity": entity,
                "count": count,
                "description": (
                    f"{entity} is connected to {count} other "
                    "entities in the stored evidence."
                ),
            })

    # Indicator 2: Multiple transaction associations
    transaction_counts = Counter()

    for relationship in relationships:
        if relationship.get("relationship_type") in {
            "ASSOCIATED_WITH_TRANSACTION",
            "INVOLVED_IN_TRANSACTION",
        }:
            source = relationship.get("source_entity_text")

            if source:
                transaction_counts[source] += 1

    for entity, count in transaction_counts.items():
        if count >= 2:
            patterns.append({
                "type": "MULTIPLE_TRANSACTION_ASSOCIATIONS",
                "entity": entity,
                "count": count,
                "description": (
                    f"{entity} is associated with {count} transactions "
                    "in the stored evidence."
                ),
            })

    return patterns