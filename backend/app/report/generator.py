"""
Renders a research project's insights into a PDF using reportlab (spec §31).

Builds directly from persisted ORM objects, returns the PDF as raw bytes (so the
API can stream it without touching disk), always includes the synthetic-data
disclaimer, and raises ReportGenerationError on failure so the API returns a
clean error envelope instead of a stack trace.
"""

import io
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.exceptions import ReportGenerationError

DISCLAIMER = (
    "This report is generated from AI-simulated personas and should be treated as "
    "exploratory research rather than statistically representative user research."
)


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="H1Custom",
            fontSize=20,
            leading=24,
            spaceAfter=14,
            textColor=colors.HexColor("#1F2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2Custom",
            fontSize=14,
            leading=18,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(ParagraphStyle(name="BodyCustom", fontSize=10.5, leading=15))
    styles.add(ParagraphStyle(name="Meta", fontSize=9, textColor=colors.grey))
    styles.add(
        ParagraphStyle(
            name="Disclaimer",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#92400E"),
            backColor=colors.HexColor("#FEF3C7"),
            borderPadding=6,
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    return styles


def _p(text, style):
    return Paragraph(escape(str(text)), style)


def _p_labeled(label, value, style):
    return Paragraph(f"<b>{escape(str(label))}:</b> {escape(str(value))}", style)


def generate_report_pdf(project, personas, questions, report) -> bytes:
    """Return the report PDF as bytes. All args are ORM objects (report may be None)."""
    try:
        buffer = io.BytesIO()
        styles = _styles()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            title="Synthetic User Research Report",
        )
        story = []

        story.append(Paragraph("Synthetic User Research Report", styles["H1Custom"]))
        story.append(
            Paragraph(
                f"Generated {datetime.now(UTC).strftime('%d %b %Y, %H:%M UTC')}", styles["Meta"]
            )
        )
        story.append(Paragraph(DISCLAIMER, styles["Disclaimer"]))
        story.append(Spacer(1, 8))

        story.append(Paragraph("Research Context", styles["H2Custom"]))
        story.append(_p_labeled("Project", project.title, styles["BodyCustom"]))
        story.append(_p_labeled("Product", project.product_description, styles["BodyCustom"]))
        story.append(_p_labeled("Target audience", project.target_audience, styles["BodyCustom"]))
        story.append(_p_labeled("Research goal", project.research_goal, styles["BodyCustom"]))
        story.append(_p_labeled("Personas simulated", len(personas), styles["BodyCustom"]))
        story.append(_p_labeled("Survey questions", len(questions), styles["BodyCustom"]))

        if report is not None:
            story.append(Paragraph("Executive Summary", styles["H2Custom"]))
            story.append(_p(report.executive_summary, styles["BodyCustom"]))
            story.append(
                _p_labeled(
                    "Overall sentiment", report.overall_sentiment.upper(), styles["BodyCustom"]
                )
            )

        # Personas table
        story.append(Paragraph("Personas Surveyed (synthetic)", styles["H2Custom"]))
        table_data = [["Name", "Occupation", "Tech-savvy", "Key pain point"]]
        for p in personas:
            table_data.append(
                [
                    p.name,
                    p.occupation,
                    p.tech_savviness,
                    (p.pain_points[0] if p.pain_points else "-"),
                ]
            )
        t = Table(table_data, hAlign="LEFT", colWidths=[3.2 * cm, 5.5 * cm, 2.3 * cm, 5.5 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F9FAFB")],
                    ),
                ]
            )
        )
        story.append(t)

        if report is not None:
            if report.themes:
                story.append(Paragraph("Key Themes", styles["H2Custom"]))
                for theme in report.themes:
                    title = escape(theme.title)
                    prevalence = escape(theme.prevalence)
                    story.append(
                        Paragraph(
                            f"<b>{title}</b> (prevalence: {prevalence})", styles["BodyCustom"]
                        )
                    )
                    story.append(_p(theme.description, styles["BodyCustom"]))
                    if theme.supporting_persona_ids:
                        supporters = escape(", ".join(theme.supporting_persona_ids))
                        story.append(
                            Paragraph(f"<i>Supported by: {supporters}</i>", styles["Meta"])
                        )
                    story.append(Spacer(1, 6))

            if report.notable_quotes:
                story.append(Paragraph("Notable Quotes", styles["H2Custom"]))
                story.append(
                    ListFlowable(
                        [ListItem(_p(q, styles["BodyCustom"])) for q in report.notable_quotes],
                        bulletType="bullet",
                    )
                )

            if report.weak_areas_or_risks:
                story.append(Paragraph("Weak Areas / Risks", styles["H2Custom"]))
                story.append(
                    ListFlowable(
                        [ListItem(_p(w, styles["BodyCustom"])) for w in report.weak_areas_or_risks],
                        bulletType="bullet",
                    )
                )

            if report.recommendations:
                story.append(Paragraph("Recommendations", styles["H2Custom"]))
                story.append(
                    ListFlowable(
                        [ListItem(_p(r, styles["BodyCustom"])) for r in report.recommendations],
                        bulletType="bullet",
                    )
                )

        doc.build(story)
        return buffer.getvalue()
    except Exception as exc:  # noqa: BLE001
        raise ReportGenerationError("Failed to generate the PDF report.") from exc
