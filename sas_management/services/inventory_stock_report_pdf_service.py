"""Ingredient Stock Report PDF generation (ReportLab, branded-ish)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Iterable, Optional

from flask import current_app, has_app_context


def _ensure_reportlab() -> bool:
    try:
        from sas_management.utils.pdf_dependencies import ensure_reportlab_installed

        logger = current_app.logger if has_app_context() else None
        return bool(ensure_reportlab_installed(logger=logger))
    except Exception:
        return False


def _money(amount, currency_prefix: Optional[str] = None) -> str:
    cur = currency_prefix or current_app.config.get("CURRENCY_PREFIX", "UGX ")
    try:
        return f"{cur}{Decimal(str(amount or 0)):,.2f}"
    except Exception:
        return f"{cur}0.00"


def _load_logo(width_inch: float = 1.0, height_inch: float = 1.0):
    """Return a ReportLab Image for the SAS logo, or None."""
    try:
        import os
        from reportlab.platypus import Image
        from reportlab.lib.units import inch

        for fn in ("sas_logo.png", "ssas_logo.png"):
            logo_path = os.path.join(current_app.static_folder or "", "images", fn)
            if os.path.exists(logo_path):
                return Image(logo_path, width=width_inch * inch, height=height_inch * inch)
    except Exception:
        return None
    return None


def generate_ingredient_stock_report_pdf_bytes(
    *,
    ingredients: Iterable,
    low_stock: Iterable,
    threshold,
    total_value,
    currency_prefix: Optional[str] = None,
    generated_at: Optional[datetime] = None,
) -> bytes:
    """Generate a PDF report for ingredient stock."""
    if not _ensure_reportlab():
        raise ImportError("PDF engine unavailable")

    ingredients = list(ingredients or [])
    low_stock = list(low_stock or [])

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    SAS_ORANGE = colors.HexColor("#F26822")
    BORDER = colors.HexColor("#e0e0e0")
    MUTED = colors.HexColor("#6c757d")

    gen_dt = generated_at or datetime.utcnow()
    cur = currency_prefix or current_app.config.get("CURRENCY_PREFIX", "UGX ")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.45 * inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=18,
        fontName="Helvetica-Bold",
        textColor=SAS_ORANGE,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    th_style = ParagraphStyle(
        "TH",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=colors.black,
    )
    td_style = ParagraphStyle("TD", parent=styles["Normal"], fontSize=9, textColor=colors.black)
    right_td_style = ParagraphStyle("TD_R", parent=td_style, alignment=TA_RIGHT)

    story = []

    # Header
    logo = _load_logo()
    if logo:
        header_tbl = Table([[logo, Paragraph("SAS BEST FOODS", ParagraphStyle("H", parent=styles["Normal"], fontSize=16, fontName="Helvetica-Bold", textColor=SAS_ORANGE, alignment=TA_RIGHT))]], colWidths=[1.0 * inch, 6.0 * inch])
        header_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        story.append(header_tbl)
        story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("INGREDIENT STOCK REPORT", title_style))
    story.append(Paragraph(f"Generated {gen_dt.strftime('%b %d, %Y %H:%M UTC')} • Low-stock threshold: {threshold}", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SAS_ORANGE, spaceAfter=0.18 * inch))

    # Summary
    summary_tbl = Table(
        [
            [Paragraph("Total Ingredients", th_style), Paragraph(str(len(ingredients)), right_td_style)],
            [Paragraph("Low Stock Items", th_style), Paragraph(str(len(low_stock)), right_td_style)],
            [Paragraph("Total Stock Value", th_style), Paragraph(_money(total_value, cur), right_td_style)],
        ],
        colWidths=[3.0 * inch, 4.0 * inch],
    )
    summary_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_tbl)
    story.append(Spacer(1, 0.2 * inch))

    # Stock table
    rows = [
        [Paragraph("Ingredient", th_style), Paragraph("Unit", th_style), Paragraph("Stock", th_style), Paragraph("Unit Cost", th_style), Paragraph("Value", th_style)]
    ]
    for i in ingredients:
        stock = Decimal(str(getattr(i, "stock_count", 0) or 0))
        unit_cost = Decimal(str(getattr(i, "unit_cost_ugx", 0) or 0))
        value = stock * unit_cost
        rows.append(
            [
                Paragraph(str(getattr(i, "name", "") or ""), td_style),
                Paragraph(str(getattr(i, "unit_of_measure", "") or ""), td_style),
                Paragraph(f"{stock:,.2f}", right_td_style),
                Paragraph(_money(unit_cost, cur), right_td_style),
                Paragraph(_money(value, cur), right_td_style),
            ]
        )

    tbl = Table(rows, colWidths=[2.7 * inch, 0.8 * inch, 1.0 * inch, 1.2 * inch, 1.3 * inch])
    tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8f9fa")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                ("TOPPADDING", (0, 1), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ]
        )
    )
    story.append(tbl)

    # Footer note
    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph("SAS Best Foods • Inventory Stock Report", ParagraphStyle("F", parent=meta_style, textColor=MUTED)))

    doc.build(story)
    return buf.getvalue()

