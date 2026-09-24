from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors


def generate_report(evidence, entities, relationships, patterns):
    """Generate a structured investigation report."""

    report = {
        "title": "AI Investigation Assistant Report",
        "generated_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "summary": {
            "evidence_files": len(evidence),
            "total_entities": len(entities),
            "total_relationships": len(relationships),
            "detected_patterns": len(patterns),
        },

        "evidence": [],
        "entities": [],
        "relationships": [],
        "patterns": patterns,
    }

    # Evidence
    for item in evidence:
        if hasattr(item, "to_dict"):
            report["evidence"].append(item.to_dict())
        elif isinstance(item, dict):
            report["evidence"].append(item)

    # Entities
    for entity in entities:
        if isinstance(entity, dict):
            report["entities"].append({
                "entity_text": entity.get("entity_text"),
                "entity_type": entity.get("entity_type"),
                "evidence_id": entity.get("evidence_id"),
                "source_filename": entity.get("source_filename"),
                "record_number": entity.get("record_number"),
                "page_number": entity.get("page_number"),
            })

    # Relationships
    for relationship in relationships:
        if isinstance(relationship, dict):
            report["relationships"].append({
                "source": relationship.get(
                    "source_entity_text"
                ),
                "source_type": relationship.get(
                    "source_entity_type"
                ),
                "relationship_type": relationship.get(
                    "relationship_type"
                ),
                "target": relationship.get(
                    "target_entity_text"
                ),
                "target_type": relationship.get(
                    "target_entity_type"
                ),
                "evidence_id": relationship.get(
                    "evidence_id"
                ),
                "source_filename": relationship.get(
                    "source_filename"
                ),
                "record_number": relationship.get(
                    "record_number"
                ),
                "page_number": relationship.get(
                    "page_number"
                ),
                "confidence": relationship.get(
                    "confidence"
                ),
            })

    return report


def generate_pdf(report):
    """Generate a downloadable PDF from a structured report."""

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    story = []

    # Title
    story.append(
        Paragraph(
            report["title"],
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            f"Generated: {report['generated_at']}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 20))

    # Summary
    story.append(
        Paragraph(
            "Investigation Summary",
            styles["Heading2"],
        )
    )

    summary = report["summary"]

    summary_data = [
        ["Metric", "Count"],
        ["Evidence Files", summary["evidence_files"]],
        ["Entities", summary["total_entities"]],
        ["Relationships", summary["total_relationships"]],
        ["Investigation Indicators", summary["detected_patterns"]],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[280, 120],
    )

    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )

    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Evidence
    story.append(
        Paragraph(
            "Evidence Sources",
            styles["Heading2"],
        )
    )

    if report["evidence"]:
        for item in report["evidence"]:
            filename = item.get(
                "original_filename",
                "Unknown",
            )

            evidence_id = item.get(
                "evidence_id",
                "Unknown",
            )

            story.append(
                Paragraph(
                    f"<b>{filename}</b> — Evidence ID: {evidence_id}",
                    styles["Normal"],
                )
            )
    else:
        story.append(
            Paragraph(
                "No evidence available.",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 15))

    # Entities
    story.append(
        Paragraph(
            "Extracted Entities",
            styles["Heading2"],
        )
    )

    if report["entities"]:
        entity_data = [
            ["Entity", "Type", "Evidence ID"]
        ]

        for entity in report["entities"][:100]:
            entity_data.append([
                str(entity.get("entity_text", "")),
                str(entity.get("entity_type", "")),
                str(entity.get("evidence_id", "")),
            ])

        entity_table = Table(
            entity_data,
            colWidths=[170, 100, 130],
            repeatRows=1,
        )

        entity_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )

        story.append(entity_table)
    else:
        story.append(
            Paragraph(
                "No entities available.",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 15))

    # Relationships
    story.append(
        Paragraph(
            "Relationships",
            styles["Heading2"],
        )
    )

    if report["relationships"]:
        relationship_data = [
            ["Source", "Relationship", "Target"]
        ]

        for relationship in report["relationships"][:100]:
            relationship_data.append([
                str(relationship.get("source", "")),
                str(
                    relationship.get(
                        "relationship_type",
                        "",
                    )
                ),
                str(relationship.get("target", "")),
            ])

        relationship_table = Table(
            relationship_data,
            colWidths=[150, 140, 150],
            repeatRows=1,
        )

        relationship_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )

        story.append(relationship_table)
    else:
        story.append(
            Paragraph(
                "No relationships available.",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 15))

    # Investigation indicators
    story.append(
        Paragraph(
            "Investigation Indicators",
            styles["Heading2"],
        )
    )

    if report["patterns"]:
        for pattern in report["patterns"]:
            story.append(
                Paragraph(
                    f"<b>{pattern.get('type', '')}</b> — "
                    f"{pattern.get('description', '')}",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 5))
    else:
        story.append(
            Paragraph(
                "No evidence-based investigation indicators detected.",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 20))

    # Disclaimer
    story.append(
        Paragraph(
            "<b>Note:</b> This report summarizes stored evidence, "
            "extracted entities, relationships, and descriptive "
            "investigation indicators. It does not determine guilt "
            "or wrongdoing and requires investigator review.",
            styles["Normal"],
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()