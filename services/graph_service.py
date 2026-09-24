"""
Knowledge graph service (Phase 4).

Builds a NetworkX graph strictly from STORED relationships
(services/relationship_store.py) — it never generates or infers new
relationships itself. Every edge stays attached to the evidence that
justified it, so the graph is always traceable back to source.
"""

import networkx as nx


def build_graph(relationships: list) -> nx.MultiDiGraph:
    """
    Nodes are entities (keyed by entity_id), edges are relationships.
    A MultiDiGraph is used because the same two entities can be linked
    by more than one relationship (e.g. from two different evidence
    files) and each must remain a distinct, traceable edge.
    """
    G = nx.MultiDiGraph()

    for r in relationships:
        G.add_node(
            r["source_entity_id"],
            entity_id=r["source_entity_id"],
            entity_text=r["source_entity_text"],
            entity_type=r["source_entity_type"],
        )
        G.add_node(
            r["target_entity_id"],
            entity_id=r["target_entity_id"],
            entity_text=r["target_entity_text"],
            entity_type=r["target_entity_type"],
        )
        G.add_edge(
            r["source_entity_id"],
            r["target_entity_id"],
            key=r["relationship_id"],
            relationship_id=r["relationship_id"],
            relationship_type=r["relationship_type"],
            evidence_id=r["evidence_id"],
            source_filename=r["source_filename"],
            record_number=r.get("record_number"),
            page_number=r.get("page_number"),
            method=r.get("method"),
            confidence=r.get("confidence"),
        )

    return G


def graph_summary(G: nx.MultiDiGraph) -> dict:
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
    }


def find_entity_nodes(G: nx.MultiDiGraph, search_text: str) -> list:
    """Case-insensitive substring match on entity_text. Returns a list of
    (node_id, entity_text, entity_type) tuples — may be more than one
    match (e.g. the same name appearing with different entity_ids)."""
    if not search_text or not search_text.strip():
        return []
    needle = search_text.strip().lower()
    return [
        (node_id, data.get("entity_text", ""), data.get("entity_type", ""))
        for node_id, data in G.nodes(data=True)
        if needle in data.get("entity_text", "").lower()
    ]


def get_connections(G: nx.MultiDiGraph, node_id: str) -> list:
    """
    Returns every relationship touching this node, in either direction,
    each annotated with the OTHER entity involved and the direction —
    this is what powers "Find Connections for an Entity".
    """
    connections = []

    for _, target_id, data in G.out_edges(node_id, data=True):
        target_data = G.nodes[target_id]
        connections.append({
            **data,
            "direction": "outgoing",
            "other_entity_id": target_id,
            "other_entity_text": target_data.get("entity_text", ""),
            "other_entity_type": target_data.get("entity_type", ""),
        })

    for source_id, _, data in G.in_edges(node_id, data=True):
        source_data = G.nodes[source_id]
        connections.append({
            **data,
            "direction": "incoming",
            "other_entity_id": source_id,
            "other_entity_text": source_data.get("entity_text", ""),
            "other_entity_type": source_data.get("entity_type", ""),
        })

    return connections
