"""Production Budget PDF generation (ReportLab, branded).

This PDF is used for printing approved production budgets with SAS branding
and the SAS logo watermark.
"""

from __future__ import annotations

import os
from decimal import Decimal
from io import BytesIO
from typing import Optional

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


def _load_logo(width_inch: float = 1.2, height_inch: float = 1.2):
    """Return a ReportLab Image for the SAS logo, or None."""
    try:
        from reportlab.platypus import Image
        from reportlab.lib.units import inch

        for fn in ("sas_logo.png", "ssas_logo.png"):
            logo_path = os.path.join(current_app.static_folder or "", "images", fn)
            if os.path.exists(logo_path):
                try:
                    # Use PIL if available (handles PNG alpha)
                    from PIL import Image as PILImage  # type: ignore

                    pil_img = PILImage.open(logo_path)
                    if pil_img.mode in ("RGBA", "LA", "P"):
                        from io import BytesIO

                        rgb_img = PILImage.new("RGB", pil_img.size, (255, 255, 255))
                        if pil_img.mode == "P":
                            pil_img = pil_img.convert("RGBA")
                        rgb_img.paste(pil_img, mask=pil_img.split()[-1] if pil_img.mode == "RGBA" else None)
                        pil_img = rgb_img
                        buf = BytesIO()
                        pil_img.save(buf, format="PNG")
                        buf.seek(0)
                        return Image(buf, width=width_inch * inch, height=height_inch * inch)
                except Exception:
                    return Image(logo_path, width=width_inch * inch, height=height_inch * inch)
    except Exception:
        return None
    return None


def generate_production_budget_pdf_bytes(budget) -> bytes:
    """Generate a branded PDF for a ProductionBudget."""
    if not _ensure_reportlab():
        raise ImportError("PDF engine unavailable")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER

    # SAS Brand Colors (match invoice PDFs)
    SAS_ORANGE = colors.HexColor("#F26822")
    SAS_LIGHT_GRAY = colors.HexColor("#f8f9fa")
    SAS_DARK_GRAY = colors.HexColor("#6c757d")
    SAS_BORDER = colors.HexColor("#e0e0e0")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.4 * inch,
        title=f"Production Budget {getattr(budget, 'id', '')}",
    )
    styles = getSampleStyleSheet()
    story = []

    # Header (logo left, company info right)
    logo_img = _load_logo()
    company_name_style = ParagraphStyle(
        "CompanyName",
        parent=styles["Normal"],
        fontSize=24,
        textColor=SAS_ORANGE,
        fontName="Helvetica-Bold",
        leading=28,
        spaceAfter=4,
    )
    company_tagline_style = ParagraphStyle(
        "CompanyTagline",
        parent=styles["Normal"],
        fontSize=11,
        textColor=SAS_ORANGE,
        fontName="Helvetica",
        leading=13,
        spaceAfter=2,
    )
    company_address_style = ParagraphStyle(
        "CompanyAddress",
        parent=styles["Normal"],
        fontSize=9,
        textColor=SAS_DARK_GRAY,
        fontName="Helvetica",
        leading=11,
        spaceAfter=1,
    )
    company_info = [
        Paragraph("SAS BEST FOODS", company_name_style),
        Paragraph("Catering & Event Management", company_tagline_style),
        Paragraph("Near Akamwesi Mall, Gayaza Rd, Opp Electoral Commission", company_address_style),
        Paragraph("Kawempe, Kampala, Uganda", company_address_style),
        Paragraph("Tel: 0702060778 / 0745705088 | www.sasbestfoods.com", company_address_style),
    ]
    header_cell = Table([[item] for item in company_info], colWidths=[5.5 * inch])
    header_cell.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    header_table = Table([[logo_img or "", header_cell]], colWidths=[1.5 * inch, 5.5 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 0.25 * inch))

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontSize=20,
        textColor=SAS_ORANGE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    story.append(Paragraph("PRODUCTION BUDGET", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SAS_ORANGE, spaceAfter=0.2 * inch))
    story.append(Spacer(1, 0.15 * inch))

    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=SAS_ORANGE,
        fontName="Helvetica-Bold",
        spaceAfter=6,
        spaceBefore=8,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=SAS_DARK_GRAY,
        fontName="Helvetica-Bold",
        spaceAfter=2,
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.black,
        fontName="Helvetica",
        spaceAfter=8,
    )
    amount_style = ParagraphStyle(
        "Amount",
        parent=styles["Normal"],
        fontSize=18,
        textColor=SAS_ORANGE,
        fontName="Helvetica-Bold",
        spaceAfter=8,
    )

    event = getattr(budget, "event", None)
    event_name = (
        getattr(event, "title", None)
        or getattr(event, "event_name", None)
        or "Untitled Event"
    )
    event_date = getattr(event, "event_date", None) or getattr(event, "date", None)
    status = getattr(getattr(budget, "status", None), "value", None) or str(getattr(budget, "status", ""))

    left_data = []
    left_data.append([Paragraph("BUDGET DETAILS", section_title_style), ""])
    left_data.append([Paragraph("Budget ID:", label_style), Paragraph(str(getattr(budget, "id", "") or "N/A"), value_style)])
    left_data.append([Paragraph("Status:", label_style), Paragraph(status or "N/A", value_style)])
    submitted_at = getattr(budget, "submitted_at", None)
    reviewed_at = getattr(budget, "reviewed_at", None)
    left_data.append([Paragraph("Submitted:", label_style), Paragraph(submitted_at.strftime("%B %d, %Y %H:%M") if submitted_at else "—", value_style)])
    left_data.append([Paragraph("Reviewed:", label_style), Paragraph(reviewed_at.strftime("%B %d, %Y %H:%M") if reviewed_at else "—", value_style)])
    left_data.append(["", ""])

    total_amount = getattr(budget, "total_cost_ugx", None) or 0
    amount_text = Paragraph(_money(total_amount), amount_style)
    amount_box_style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, -1), SAS_LIGHT_GRAY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, -1), 2, SAS_ORANGE),
            ("LINEABOVE", (0, 0), (-1, -1), 2, SAS_ORANGE),
            ("LINELEFT", (0, 0), (-1, -1), 2, SAS_ORANGE),
            ("LINERIGHT", (0, 0), (-1, -1), 2, SAS_ORANGE),
        ]
    )
    amount_table = Table([[amount_text]], colWidths=[2.8 * inch])
    amount_table.setStyle(amount_box_style)
    left_data.append([amount_table, ""])

    right_data = []
    right_data.append([Paragraph("EVENT DETAILS", section_title_style), ""])
    right_data.append([Paragraph("Event:", label_style), Paragraph(str(event_name), value_style)])
    if event_date:
        right_data.append([Paragraph("Event Date:", label_style), Paragraph(event_date.strftime("%B %d, %Y"), value_style)])
    venue = getattr(event, "venue", None)
    if venue:
        right_data.append([Paragraph("Venue:", label_style), Paragraph(str(venue), value_style)])
    client = getattr(event, "client", None)
    if client:
        right_data.append(["", ""])
        right_data.append([Paragraph("CLIENT", section_title_style), ""])
        right_data.append([Paragraph("Name:", label_style), Paragraph(getattr(client, "name", None) or "N/A", value_style)])

    left_table = Table(left_data, colWidths=[1.2 * inch, 1.8 * inch])
    right_table = Table(right_data, colWidths=[1.2 * inch, 1.8 * inch])
    table_style = TableStyle(
        [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
    left_table.setStyle(table_style)
    right_table.setStyle(table_style)
    main_table = Table([[left_table, right_table]], colWidths=[3.2 * inch, 3.2 * inch])
    main_table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(main_table)
    story.append(Spacer(1, 0.2 * inch))

    # Items table
    story.append(Paragraph("BUDGET ITEMS", section_title_style))
    th = ParagraphStyle("Th", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=colors.black)
    td = ParagraphStyle("Td", parent=styles["Normal"], fontSize=9, textColor=colors.black)
    rows = [[Paragraph("Category", th), Paragraph("Description", th), Paragraph("Qty", th), Paragraph("Unit Cost", th), Paragraph("Total", th)]]
    for it in (getattr(budget, "items", None) or []):
        rows.append(
            [
                Paragraph(str(getattr(getattr(it, "category", None), "value", "") or ""), td),
                Paragraph(str(getattr(it, "description", "") or ""), td),
                Paragraph(f"{Decimal(str(getattr(it, 'quantity', 0) or 0)):,.2f}", td),
                Paragraph(_money(getattr(it, "unit_cost_ugx", 0)), td),
                Paragraph(_money(getattr(it, "total_cost_ugx", 0)), td),
            ]
        )
    items_tbl = Table(rows, colWidths=[1.15 * inch, 2.9 * inch, 0.65 * inch, 1.15 * inch, 1.15 * inch])
    items_tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, SAS_BORDER),
                ("BACKGROUND", (0, 0), (-1, 0), SAS_LIGHT_GRAY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(items_tbl)

    # Admin recommendations (if any)
    rec = getattr(budget, "admin_recommendations", None)
    if rec:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("ADMIN NOTES / RECOMMENDATIONS", section_title_style))
        story.append(Paragraph(str(rec).replace("\n", "<br/>"), ParagraphStyle("Rec", parent=value_style, leading=12)))

    # Footer + watermark
    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=SAS_BORDER, spaceAfter=0.15 * inch))
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=SAS_DARK_GRAY, alignment=TA_CENTER, spaceAfter=2)
    story.append(Paragraph("Generated by SAS Management System · SAS Best Foods", footer_style))

    from sas_management.utils.reportlab_watermark import make_center_watermark_callback

    wm = make_center_watermark_callback(static_folder=current_app.static_folder, opacity=0.12, width_ratio=0.40)
    doc.build(story, onFirstPage=wm, onLaterPages=wm)
    return buf.getvalue()


def generate_production_budget_pdf(budget) -> str:
    """Generate (and save) a ProductionBudget PDF and return the full file path."""
    out_dir = os.path.join(current_app.instance_path, "production_budgets")
    os.makedirs(out_dir, exist_ok=True)
    full_path = os.path.abspath(os.path.join(out_dir, f"production_budget_{getattr(budget, 'id', '')}.pdf"))

    pdf_bytes = generate_production_budget_pdf_bytes(budget)
    with open(full_path, "wb") as f:
        f.write(pdf_bytes)
    return full_path

