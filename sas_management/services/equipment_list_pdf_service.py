"""
Equipment List PDF Generation Service
Generates professional PDF documents for event catering equipment lists.
Matches the exact layout and branding of the SAS quotation/invoice PDFs.
"""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Optional

from flask import current_app, has_app_context


def _ensure_reportlab() -> bool:
    """Ensure ReportLab is importable (auto-installs if needed)."""
    try:
        from sas_management.utils.pdf_dependencies import ensure_reportlab_installed

        logger = current_app.logger if has_app_context() else None
        return bool(ensure_reportlab_installed(logger=logger))
    except Exception:
        return False


def _load_logo_path() -> Optional[str]:
    """Load SAS logo path."""
    try:
        static_folder = current_app.static_folder
        if not static_folder:
            return None
        for fn in ("ssas_logo.png", "sas_logo.png"):
            p = os.path.join(static_folder, "images", fn)
            if os.path.exists(p):
                return p
    except Exception:
        return None
    return None


def generate_equipment_list_pdf(equipment_list) -> str:
    """
    Generate a professional PDF for an event equipment list.
    Uses the same layout and branding as quotation/invoice PDFs.
    
    Args:
        equipment_list: EventEquipmentList object with items loaded
        
    Returns:
        str: Path to the generated PDF file
    """
    if not _ensure_reportlab():
        raise ImportError("PDF engine unavailable")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

    # Ensure output directory exists
    output_dir = os.path.join(current_app.instance_path, "equipment_lists")
    os.makedirs(output_dir, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SAS_Equipment_List_{equipment_list.event_id}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)

    # Create PDF document with same margins as quotation
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.4 * inch,
        title=f"Equipment List - {equipment_list.event.title if equipment_list.event else 'Event'}"
    )

    # SAS Brand Colors (matching quotation_service.py)
    BORDER = colors.HexColor("#b9b9b9")
    GRID = colors.HexColor("#d5d5d5")
    HEADER_BG = colors.HexColor("#efefef")
    TEXT = colors.HexColor("#111111")
    MUTED = colors.HexColor("#555555")
    SAS_ORANGE = colors.HexColor("#F26822")

    # Get styles
    styles = getSampleStyleSheet()

    # Custom styles matching quotation layout
    title_style = ParagraphStyle(
        "TitleRef",
        parent=styles["Normal"],
        fontSize=16.5,
        textColor=TEXT,
        spaceAfter=6,
        fontName="Helvetica-Bold"
    )
    company_name_style = ParagraphStyle(
        "CompanyName",
        parent=styles["Normal"],
        fontSize=12.5,
        textColor=TEXT,
        spaceAfter=2,
        fontName="Helvetica-Bold"
    )
    small_ref_style = ParagraphStyle(
        "SmallRef",
        parent=styles["Normal"],
        fontSize=8.7,
        leading=10.4,
        textColor=MUTED
    )
    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontSize=8.7,
        textColor=TEXT
    )
    meta_value_style = ParagraphStyle(
        "MetaValue",
        parent=styles["Normal"],
        fontSize=8.7,
        textColor=TEXT,
        alignment=TA_RIGHT
    )
    meta_total_label_style = ParagraphStyle(
        "MetaTotalLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        textColor=TEXT
    )
    meta_total_value_style = ParagraphStyle(
        "MetaTotalValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        textColor=TEXT,
        alignment=TA_RIGHT
    )
    meta_s = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9.5,
        textColor=TEXT
    )
    muted_s = ParagraphStyle(
        "Muted",
        parent=styles["Normal"],
        fontSize=9.5,
        textColor=MUTED
    )
    box_hdr_style = ParagraphStyle(
        "BoxHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=TEXT
    )
    th_style = ParagraphStyle(
        "Th",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.7,
        textColor=TEXT
    )
    td_style = ParagraphStyle(
        "Td",
        parent=styles["Normal"],
        fontSize=8.7,
        textColor=TEXT
    )
    td_muted_style = ParagraphStyle(
        "TdMuted",
        parent=styles["Normal"],
        fontSize=8.2,
        leading=10.0,
        textColor=MUTED
    )
    notes_hdr_style = ParagraphStyle(
        "NotesHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=TEXT
    )
    notes_body_style = ParagraphStyle(
        "NotesBody",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=10.5,
        textColor=MUTED
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8.2,
        alignment=TA_CENTER,
        textColor=MUTED
    )

    story = []

    # Get event details
    event = equipment_list.event

    # ========== HEADER (matching quotation layout) ==========
    logo_path = _load_logo_path()
    logo = None
    if logo_path:
        try:
            logo = Image(logo_path, width=24, height=24)
        except Exception:
            logo = None

    # Left block - Title and company info
    left_block = [
        Paragraph("EQUIPMENT PREPARATION LIST", title_style),
        Table(
            [[logo or "", Paragraph("SAS Best Foods", company_name_style)]],
            colWidths=[0.35 * 72, 3.7 * 72]
        ),
        Paragraph("Near Akamwesi Mall, Gayaza Rd, Opp Electoral Commission Kawempe Offices", small_ref_style),
        Paragraph("Kawempe, Kampala, Uganda", small_ref_style),
        Paragraph("Tel: 0702060778 / 0745705088", small_ref_style),
        Paragraph("Email: info@sasbestfoods.com | Website: www.sasbestfoods.com", small_ref_style),
    ]

    # Right block - Meta info box
    list_status = equipment_list.status.value if hasattr(equipment_list.status, 'value') else str(equipment_list.status)
    event_date = event.date if event and event.date else (event.event_date.date() if event and event.event_date else None)
    
    # Calculate totals
    total_items = len(equipment_list.items) if equipment_list.items else 0
    total_quantity = sum(item.quantity for item in (equipment_list.items or []))

    meta_rows = [
        ("List #", f"EQL-{equipment_list.event_id}"),
        ("Event Date", event_date.strftime("%b %d, %Y") if event_date else "N/A"),
        ("Prepared On", equipment_list.created_at.strftime("%b %d, %Y") if equipment_list.created_at else "N/A"),
        ("Status", list_status),
    ]
    
    meta_tbl = Table(
        [[Paragraph(f"<b>{k}</b>", meta_label_style), Paragraph(v, meta_value_style)] for k, v in meta_rows]
        + [[Paragraph("TOTAL ITEMS", meta_total_label_style), Paragraph(str(total_quantity), meta_total_value_style)]],
        colWidths=[1.4 * 72, 1.55 * 72]
    )
    meta_tbl.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, BORDER),
            ("INNERGRID", (0, 0), (-1, -2), 0, colors.white),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (0, -1), (-1, -1), 1, BORDER),
            ("TOPPADDING", (0, -1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
        ])
    )

    header_tbl = Table([[left_block, meta_tbl]], colWidths=[4.25 * 72, 2.95 * 72])
    header_tbl.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    story.append(header_tbl)
    story.append(Spacer(1, 10))

    # ========== EVENT & VENUE INFO (two boxes like quotation) ==========
    # Left box - Event details
    event_left = []
    if event:
        event_left.append(Paragraph(f"<b>{event.title or 'Event'}</b>", meta_s))
        if event_date:
            event_left.append(Paragraph(event_date.strftime("%A, %B %d, %Y"), muted_s))
        if event.guest_count:
            event_left.append(Paragraph(f"{event.guest_count} guests expected", muted_s))
        if event.event_type:
            event_left.append(Paragraph(f"Type: {event.event_type}", muted_s))
    else:
        event_left.append(Paragraph("No event information available", muted_s))

    # Right box - Venue & Client
    venue_right = []
    venue_name = event.venue_obj.name if event and event.venue_obj else (event.venue if event else None)
    client = event.client if event else None
    
    if venue_name:
        venue_right.append(Paragraph(f"<b>{venue_name}</b>", meta_s))
        if event and event.venue_obj and event.venue_obj.address:
            venue_right.append(Paragraph(event.venue_obj.address, muted_s))
    if client:
        venue_right.append(Paragraph(f"Client: {client.name}", muted_s))
        if client.phone:
            venue_right.append(Paragraph(f"Tel: {client.phone}", muted_s))
    if not venue_name and not client:
        venue_right.append(Paragraph("Venue & Client TBD", muted_s))

    info_tbl = Table(
        [
            [Paragraph("EVENT DETAILS", box_hdr_style), Paragraph("VENUE & CLIENT", box_hdr_style)],
            [event_left, venue_right]
        ],
        colWidths=[3.55 * 72, 3.55 * 72]
    )
    info_tbl.setStyle(
        TableStyle([
            ("BOX", (0, 0), (0, 1), 1, BORDER),
            ("BOX", (1, 0), (1, 1), 1, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            ("TOPPADDING", (0, 1), (-1, 1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ])
    )
    story.append(info_tbl)
    story.append(Spacer(1, 10))

    # ========== EQUIPMENT ITEMS TABLE ==========
    # Group items by category
    items_by_category = {}
    for item in (equipment_list.items or []):
        cat = item.category or "General"
        if cat not in items_by_category:
            items_by_category[cat] = []
        items_by_category[cat].append(item)

    if items_by_category:
        # Build items table with all items
        items_data = [
            [
                Paragraph("#", th_style),
                Paragraph("ITEM NAME", th_style),
                Paragraph("CATEGORY", th_style),
                Paragraph("QTY", th_style),
                Paragraph("NOTES", th_style),
                Paragraph("CHECK", th_style)
            ]
        ]
        
        idx = 1
        for category in sorted(items_by_category.keys()):
            for item in items_by_category[category]:
                items_data.append([
                    Paragraph(str(idx), td_style),
                    Paragraph(item.item_name, td_style),
                    Paragraph(category, td_muted_style),
                    Paragraph(str(item.quantity), td_style),
                    Paragraph(item.notes or "-", td_muted_style),
                    Paragraph("[ ]", td_style)  # Checkbox for manual checking
                ])
                idx += 1

        items_tbl = Table(items_data, colWidths=[0.4 * 72, 2.4 * 72, 1.2 * 72, 0.5 * 72, 1.6 * 72, 0.5 * 72])
        items_tbl.setStyle(
            TableStyle([
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GRID),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),  # # column
                ("ALIGN", (3, 0), (3, -1), "CENTER"),  # QTY column
                ("ALIGN", (5, 0), (5, -1), "CENTER"),  # CHECK column
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                ("TOPPADDING", (0, 1), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ])
        )
        story.append(items_tbl)
        story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("No items in this equipment list.", muted_s))
        story.append(Spacer(1, 10))

    # ========== BOTTOM: NOTES + SUMMARY (matching quotation layout) ==========
    # Notes box (left)
    notes_text = equipment_list.notes if equipment_list.notes else "Please verify all items upon loading. Report any missing or damaged items immediately."
    notes_box = Table(
        [
            [Paragraph("NOTES / INSTRUCTIONS", notes_hdr_style)],
            [Paragraph(notes_text, notes_body_style)]
        ],
        colWidths=[3.55 * 72]
    )
    notes_box.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 1), (-1, 1), 8),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ])
    )

    # Summary box (right)
    num_categories = len(items_by_category)
    summary_rows = [
        ("Categories", str(num_categories)),
        ("Total Items", str(total_items)),
        ("Total Quantity", str(total_quantity)),
    ]
    summary_tbl = Table(
        [[Paragraph(k, meta_label_style), Paragraph(v, meta_value_style)] for k, v in summary_rows[:2]]
        + [[Paragraph("<b>Total Quantity</b>", meta_label_style), Paragraph(f"<b>{total_quantity}</b>", meta_value_style)]],
        colWidths=[1.65 * 72, 1.9 * 72]
    )
    summary_tbl.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LINEABOVE", (0, 2), (-1, 2), 0.5, GRID),
        ])
    )

    bottom_tbl = Table([[notes_box, summary_tbl]], colWidths=[3.55 * 72, 3.55 * 72])
    bottom_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(bottom_tbl)
    story.append(Spacer(1, 15))

    # ========== SIGNATURES SECTION ==========
    sig_label_style = ParagraphStyle(
        "SigLabel",
        parent=styles["Normal"],
        fontSize=8,
        textColor=MUTED
    )
    
    sig_data = [
        [
            Paragraph("Prepared By:", sig_label_style),
            Paragraph("_" * 25, sig_label_style),
            Paragraph("Checked By:", sig_label_style),
            Paragraph("_" * 25, sig_label_style)
        ],
        [
            Paragraph("Name:", sig_label_style),
            Paragraph(equipment_list.creator.email if equipment_list.creator else "", td_muted_style),
            Paragraph("Name:", sig_label_style),
            Paragraph("", td_muted_style)
        ],
        [
            Paragraph("Date:", sig_label_style),
            Paragraph(equipment_list.created_at.strftime("%Y-%m-%d") if equipment_list.created_at else "", td_muted_style),
            Paragraph("Date:", sig_label_style),
            Paragraph("", td_muted_style)
        ],
    ]
    
    sig_tbl = Table(sig_data, colWidths=[0.8 * 72, 2.2 * 72, 0.8 * 72, 2.2 * 72])
    sig_tbl.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(sig_tbl)
    story.append(Spacer(1, 10))

    # ========== FOOTER ==========
    story.append(Paragraph("Generated by SAS Management System · SAS Best Foods", footer_style))

    # Build PDF with watermark (matching quotation)
    try:
        from sas_management.utils.reportlab_watermark import make_center_watermark_callback
        wm = make_center_watermark_callback(static_folder=current_app.static_folder, opacity=0.12, width_ratio=0.40)
        doc.build(story, onFirstPage=wm, onLaterPages=wm)
    except ImportError:
        # If watermark module not available, build without it
        doc.build(story)

    return output_path
