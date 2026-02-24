"""
Hire Order PDF generation for receipts and delivery notes.
Matches the style and format of event receipt PDFs.
"""

from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Optional

from flask import current_app, has_app_context


def _ensure_reportlab() -> bool:
    """Ensure ReportLab is importable."""
    try:
        from sas_management.utils.pdf_dependencies import ensure_reportlab_installed
        logger = current_app.logger if has_app_context() else None
        return bool(ensure_reportlab_installed(logger=logger))
    except Exception:
        return False


def _get_rental_days(order) -> int:
    """Calculate rental days from order dates."""
    start_date = getattr(order, 'start_date', None)
    end_date = getattr(order, 'end_date', None)
    if start_date and end_date:
        return max(1, (end_date - start_date).days + 1)
    return 1


def generate_hire_receipt_pdf(order) -> bytes:
    """
    Generate a PDF receipt for a hire order.
    Matches the style of event receipt PDFs.
    """
    if not _ensure_reportlab():
        raise ImportError("PDF engine unavailable - please install reportlab")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")

    # Extract order data
    order_ref = getattr(order, 'reference', None) or f"HO-{order.id}"
    client_name = getattr(order, 'client_name', None) or "Walk-in Client"
    telephone = getattr(order, 'telephone', None) or ""
    email = getattr(order, 'email', None) or ""
    delivery_address = getattr(order, 'delivery_address', None) or ""
    
    total_cost = Decimal(str(getattr(order, 'total_cost', 0) or 0))
    amount_paid = Decimal(str(getattr(order, 'amount_paid', 0) or 0))
    balance_due = Decimal(str(getattr(order, 'balance_due', 0) or 0))
    
    start_date = getattr(order, 'start_date', None)
    end_date = getattr(order, 'end_date', None)
    created_at = getattr(order, 'created_at', None) or datetime.now()
    rental_days = _get_rental_days(order)
    
    items = getattr(order, 'items', []) or []

    def money(v) -> str:
        return f"{CURRENCY}{Decimal(str(v or 0)):,.2f}"

    # SAS Brand Colors
    SAS_ORANGE = colors.HexColor("#F26822")
    SAS_BLACK = colors.HexColor("#222222")  # Changed from green to black
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
    )
    styles = getSampleStyleSheet()

    # Custom styles
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
        textColor=SAS_BLACK,
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
    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Normal"],
        fontSize=20,
        textColor=SAS_ORANGE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=SAS_BLACK,
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
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=SAS_DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=2,
    )

    # Logo
    logo_img = None
    try:
        for fn in ("sas_logo.png", "ssas_logo.png"):
            logo_path = os.path.join(current_app.static_folder or "", "images", fn)
            if os.path.exists(logo_path):
                logo_img = Image(logo_path, width=1.2 * inch, height=1.2 * inch)
                break
    except Exception:
        logo_img = None

    # Header
    company_info = [
        Paragraph("SAS BEST FOODS", company_name_style),
        Paragraph("Equipment Hire Division", company_tagline_style),
        Paragraph("Near Akamwesi Mall, Gayaza Rd, Opp Electoral Commission", company_address_style),
        Paragraph("Kawempe, Kampala, Uganda", company_address_style),
        Paragraph("Tel: 0702060778 / 0745705088 | www.sasbestfoods.com", company_address_style),
    ]
    header_cell = Table([[item] for item in company_info], colWidths=[5.5 * inch])
    header_cell.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    header_table = Table([[logo_img or "", header_cell]], colWidths=[1.5 * inch, 5.5 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story = [header_table, Spacer(1, 0.25 * inch)]

    # Title
    story.append(Paragraph("EQUIPMENT HIRE RECEIPT", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SAS_ORANGE, spaceAfter=0.2 * inch))
    story.append(Spacer(1, 0.15 * inch))

    # Receipt details and client info side by side
    left_data = []
    left_data.append([Paragraph("RECEIPT DETAILS", section_title_style), ""])
    left_data.append([Paragraph("Receipt #:", label_style), Paragraph(f"RCP-{order_ref}", value_style)])
    left_data.append([Paragraph("Order Ref:", label_style), Paragraph(order_ref, value_style)])
    left_data.append([Paragraph("Date:", label_style), Paragraph(created_at.strftime("%B %d, %Y") if created_at else "N/A", value_style)])
    left_data.append([Paragraph("Status:", label_style), Paragraph(getattr(order, 'status', 'Pending') or 'Pending', value_style)])
    left_data.append(["", ""])

    # Amount box
    amount_text = Paragraph(money(total_cost), amount_style)
    amount_box_style = TableStyle([
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
    ])
    amount_table = Table([[amount_text]], colWidths=[2.8 * inch])
    amount_table.setStyle(amount_box_style)
    left_data.append([amount_table, ""])

    right_data = []
    right_data.append([Paragraph("CLIENT INFORMATION", section_title_style), ""])
    right_data.append([Paragraph("Name:", label_style), Paragraph(client_name, value_style)])
    if telephone:
        right_data.append([Paragraph("Telephone:", label_style), Paragraph(telephone, value_style)])
    if email:
        right_data.append([Paragraph("Email:", label_style), Paragraph(email, value_style)])
    if delivery_address:
        right_data.append([Paragraph("Address:", label_style), Paragraph(delivery_address[:50], value_style)])
    right_data.append(["", ""])
    right_data.append([Paragraph("RENTAL PERIOD", section_title_style), ""])
    right_data.append([Paragraph("Start Date:", label_style), Paragraph(start_date.strftime("%B %d, %Y") if start_date else "N/A", value_style)])
    right_data.append([Paragraph("End Date:", label_style), Paragraph(end_date.strftime("%B %d, %Y") if end_date else "N/A", value_style)])
    right_data.append([Paragraph("Duration:", label_style), Paragraph(f"{rental_days} day{'s' if rental_days != 1 else ''}", value_style)])

    left_table = Table(left_data, colWidths=[1.2 * inch, 1.8 * inch])
    right_table = Table(right_data, colWidths=[1.2 * inch, 1.8 * inch])
    table_style = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])
    left_table.setStyle(table_style)
    right_table.setStyle(table_style)
    main_table = Table([[left_table, right_table]], colWidths=[3.2 * inch, 3.2 * inch])
    main_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(main_table)
    story.append(Spacer(1, 0.2 * inch))

    # Items table
    story.append(Paragraph("HIRED ITEMS", section_title_style))
    items_data = [["Item", "Qty", "Unit Price", "Days", "Subtotal"]]
    for item in items:
        inv_item = getattr(item, 'inventory_item', None)
        item_name = getattr(inv_item, 'name', None) if inv_item else f"Item #{getattr(item, 'item_id', '')}"
        qty = getattr(item, 'qty', 1) or 1
        price = Decimal(str(getattr(item, 'price', 0) or 0))
        subtotal = Decimal(str(getattr(item, 'subtotal', 0) or 0))
        items_data.append([
            item_name or "Unknown Item",
            str(qty),
            money(price),
            str(rental_days),
            money(subtotal)
        ])

    if len(items_data) == 1:
        items_data.append(["No items", "", "", "", ""])

    items_table = Table(items_data, colWidths=[2.5 * inch, 0.6 * inch, 1.2 * inch, 0.7 * inch, 1.4 * inch])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SAS_BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, SAS_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.15 * inch))

    # Totals
    totals_data = [
        ["Subtotal:", money(total_cost)],
        ["Amount Paid:", money(amount_paid)],
        ["Balance Due:", money(balance_due)],
    ]
    totals_table = Table(totals_data, colWidths=[5.0 * inch, 1.4 * inch])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEABOVE", (0, -1), (-1, -1), 1, SAS_ORANGE),
        ("TEXTCOLOR", (1, -1), (1, -1), SAS_ORANGE if balance_due > 0 else SAS_BLACK),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.2 * inch))

    # Payment status
    if amount_paid >= total_cost:
        status_text = "PAID IN FULL"
        status_color = SAS_BLACK
    elif amount_paid > 0:
        status_text = "PARTIAL PAYMENT"
        status_color = colors.HexColor("#ffc107")
    else:
        status_text = "UNPAID"
        status_color = colors.HexColor("#dc3545")

    status_style = ParagraphStyle(
        "Status",
        parent=styles["Normal"],
        fontSize=14,
        textColor=status_color,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    story.append(Paragraph(status_text, status_style))
    story.append(Spacer(1, 0.2 * inch))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=SAS_BORDER, spaceAfter=0.15 * inch))
    story.append(Paragraph("All hired equipment must be returned in the same condition as received.", footer_style))
    story.append(Paragraph("Client is responsible for any damage or loss during the rental period.", footer_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Thank you for choosing SAS Best Foods Equipment Hire!", footer_style))

    # Build with watermark
    try:
        from sas_management.utils.reportlab_watermark import make_center_watermark_callback
        wm = make_center_watermark_callback(static_folder=current_app.static_folder, opacity=0.12, width_ratio=0.40)
        doc.build(story, onFirstPage=wm, onLaterPages=wm)
    except Exception:
        doc.build(story)

    return buf.getvalue()


def generate_hire_delivery_note_pdf(order) -> bytes:
    """
    Generate a PDF delivery note for a hire order.
    Matches the style of event receipt PDFs.
    """
    if not _ensure_reportlab():
        raise ImportError("PDF engine unavailable - please install reportlab")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")

    # Extract order data
    order_ref = getattr(order, 'reference', None) or f"HO-{order.id}"
    client_name = getattr(order, 'client_name', None) or "Walk-in Client"
    telephone = getattr(order, 'telephone', None) or ""
    email = getattr(order, 'email', None) or ""
    delivery_address = getattr(order, 'delivery_address', None) or ""
    
    start_date = getattr(order, 'start_date', None)
    end_date = getattr(order, 'end_date', None)
    delivery_date = getattr(order, 'delivery_date', None) or start_date
    pickup_date = getattr(order, 'pickup_date', None) or end_date
    rental_days = _get_rental_days(order)
    
    items = getattr(order, 'items', []) or []

    # SAS Brand Colors
    SAS_ORANGE = colors.HexColor("#F26822")
    SAS_BLACK = colors.HexColor("#222222")
    SAS_LIGHT_GRAY = colors.HexColor("#f8f9fa")
    SAS_DARK_GRAY = colors.HexColor("#6c757d")
    SAS_BORDER = colors.HexColor("#e0e0e0")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    company_name_style = ParagraphStyle(
        "CompanyName",
        parent=styles["Normal"],
        fontSize=22,
        textColor=SAS_ORANGE,
        fontName="Helvetica-Bold",
        leading=26,
        spaceAfter=4,
    )
    company_tagline_style = ParagraphStyle(
        "CompanyTagline",
        parent=styles["Normal"],
        fontSize=10,
        textColor=SAS_BLACK,
        fontName="Helvetica",
        leading=12,
        spaceAfter=2,
    )
    company_address_style = ParagraphStyle(
        "CompanyAddress",
        parent=styles["Normal"],
        fontSize=8,
        textColor=SAS_DARK_GRAY,
        fontName="Helvetica",
        leading=10,
        spaceAfter=1,
    )
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=18,
        textColor=SAS_ORANGE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=SAS_BLACK,
        fontName="Helvetica-Bold",
        spaceAfter=4,
        spaceBefore=6,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=8,
        textColor=SAS_DARK_GRAY,
        fontName="Helvetica-Bold",
        spaceAfter=2,
    )
    value_style = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.black,
        fontName="Helvetica",
        spaceAfter=6,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=7,
        textColor=SAS_DARK_GRAY,
        alignment=TA_LEFT,
        spaceAfter=2,
    )

    # Logo
    logo_img = None
    try:
        for fn in ("sas_logo.png", "ssas_logo.png"):
            logo_path = os.path.join(current_app.static_folder or "", "images", fn)
            if os.path.exists(logo_path):
                logo_img = Image(logo_path, width=1.0 * inch, height=1.0 * inch)
                break
    except Exception:
        logo_img = None

    # Header
    company_info = [
        Paragraph("SAS BEST FOODS", company_name_style),
        Paragraph("Equipment Hire Division", company_tagline_style),
        Paragraph("Near Akamwesi Mall, Gayaza Rd, Kawempe, Kampala", company_address_style),
        Paragraph("Tel: 0702060778 / 0745705088", company_address_style),
    ]
    header_cell = Table([[item] for item in company_info], colWidths=[5.5 * inch])
    header_cell.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    header_table = Table([[logo_img or "", header_cell]], colWidths=[1.2 * inch, 5.8 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))

    story = [header_table, Spacer(1, 0.15 * inch)]

    # Title
    story.append(Paragraph("DELIVERY NOTE", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SAS_ORANGE, spaceAfter=0.15 * inch))

    # Delivery note details and client info side by side
    left_data = []
    left_data.append([Paragraph("DELIVERY DETAILS", section_title_style), ""])
    left_data.append([Paragraph("DN Number:", label_style), Paragraph(f"DN-{order_ref}", value_style)])
    left_data.append([Paragraph("Order Ref:", label_style), Paragraph(order_ref, value_style)])
    left_data.append([Paragraph("Issue Date:", label_style), Paragraph(datetime.now().strftime("%B %d, %Y"), value_style)])
    left_data.append([Paragraph("Delivery Date:", label_style), Paragraph(delivery_date.strftime("%B %d, %Y") if delivery_date else "N/A", value_style)])
    left_data.append([Paragraph("Return Date:", label_style), Paragraph(pickup_date.strftime("%B %d, %Y") if pickup_date else "N/A", value_style)])

    right_data = []
    right_data.append([Paragraph("DELIVER TO", section_title_style), ""])
    right_data.append([Paragraph("Name:", label_style), Paragraph(client_name, value_style)])
    if telephone:
        right_data.append([Paragraph("Telephone:", label_style), Paragraph(telephone, value_style)])
    if email:
        right_data.append([Paragraph("Email:", label_style), Paragraph(email, value_style)])
    if delivery_address:
        addr_short = delivery_address[:60] + "..." if len(delivery_address) > 60 else delivery_address
        right_data.append([Paragraph("Address:", label_style), Paragraph(addr_short, value_style)])
    right_data.append([Paragraph("Rental Period:", label_style), Paragraph(f"{rental_days} day{'s' if rental_days != 1 else ''}", value_style)])

    left_table = Table(left_data, colWidths=[1.0 * inch, 2.0 * inch])
    right_table = Table(right_data, colWidths=[1.0 * inch, 2.5 * inch])
    table_style = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ])
    left_table.setStyle(table_style)
    right_table.setStyle(table_style)
    main_table = Table([[left_table, right_table]], colWidths=[3.2 * inch, 3.8 * inch])
    main_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(main_table)
    story.append(Spacer(1, 0.15 * inch))

    # Items table with condition columns
    story.append(Paragraph("EQUIPMENT LIST", section_title_style))
    items_data = [["", "Item Description", "Qty", "Condition Out", "Condition In", "Notes"]]
    
    for idx, item in enumerate(items, 1):
        inv_item = getattr(item, 'inventory_item', None)
        item_name = getattr(inv_item, 'name', None) if inv_item else f"Item #{getattr(item, 'item_id', '')}"
        category = getattr(inv_item, 'category', '') if inv_item else ''
        sku = getattr(inv_item, 'sku', '') if inv_item else ''
        qty = getattr(item, 'qty', 1) or 1
        
        desc = item_name or "Unknown Item"
        if category:
            desc += f"\n({category})"
        if sku:
            desc += f"\nSKU: {sku}"
        
        items_data.append([
            str(idx),
            desc,
            str(qty),
            "",  # Condition Out - to be filled manually
            "",  # Condition In - to be filled manually
            "",  # Notes - to be filled manually
        ])

    if len(items_data) == 1:
        items_data.append(["", "No items", "", "", "", ""])

    # Calculate total items
    total_qty = sum(getattr(item, 'qty', 1) or 1 for item in items)
    items_data.append(["", "TOTAL ITEMS", str(total_qty), "", "", ""])

    items_table = Table(items_data, colWidths=[0.3 * inch, 2.5 * inch, 0.5 * inch, 1.0 * inch, 1.0 * inch, 1.2 * inch])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SAS_BLACK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, SAS_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, -1), (-1, -1), SAS_LIGHT_GRAY),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.1 * inch))

    # Condition guide
    guide_style = ParagraphStyle("Guide", parent=styles["Normal"], fontSize=7, textColor=SAS_DARK_GRAY)
    story.append(Paragraph("<b>Condition Guide:</b> E = Excellent | G = Good | F = Fair | P = Poor | D = Damaged | M = Missing", guide_style))
    story.append(Spacer(1, 0.15 * inch))

    # Signature section
    story.append(Paragraph("AUTHORIZATION SIGNATURES", section_title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=SAS_BORDER, spaceAfter=0.1 * inch))

    sig_label_style = ParagraphStyle("SigLabel", parent=styles["Normal"], fontSize=8, textColor=SAS_DARK_GRAY, fontName="Helvetica-Bold")
    sig_line_style = ParagraphStyle("SigLine", parent=styles["Normal"], fontSize=8, textColor=colors.black)

    sig_data = [
        [Paragraph("<b>ISSUED BY (SAS Staff)</b>", sig_label_style), Paragraph("<b>RECEIVED BY (Client)</b>", sig_label_style)],
        [Paragraph("I confirm all items have been checked and released.", sig_line_style), Paragraph("I confirm receipt and agree to return in same condition.", sig_line_style)],
        ["", ""],
        [Paragraph("Name: _______________________", sig_line_style), Paragraph("Name: _______________________", sig_line_style)],
        ["", ""],
        [Paragraph("Signature: ___________________", sig_line_style), Paragraph("Signature: ___________________", sig_line_style)],
        ["", ""],
        [Paragraph("Date: _________ Time: ________", sig_line_style), Paragraph("Date: _________ ID/Phone: ________", sig_line_style)],
    ]
    sig_table = Table(sig_data, colWidths=[3.4 * inch, 3.4 * inch])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (0, -1), 1, SAS_BORDER),
        ("BOX", (1, 0), (1, -1), 1, SAS_BORDER),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 0.15 * inch))

    # Return section
    story.append(Paragraph("RETURN AUTHORIZATION", section_title_style))
    return_data = [
        [Paragraph("<b>RECEIVED BY (SAS Staff)</b>", sig_label_style), Paragraph("<b>RETURNED BY (Client)</b>", sig_label_style)],
        [Paragraph("Name & Signature: _____________", sig_line_style), Paragraph("Name & Signature: _____________", sig_line_style)],
        [Paragraph("Date & Time: _________________", sig_line_style), Paragraph("Date & Time: _________________", sig_line_style)],
    ]
    return_table = Table(return_data, colWidths=[3.4 * inch, 3.4 * inch])
    return_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 1, SAS_BORDER),
    ]))
    story.append(return_table)
    story.append(Spacer(1, 0.1 * inch))

    # Damage notes
    story.append(Paragraph("Damage/Missing Items (if any): _______________________________________________", sig_line_style))
    story.append(Spacer(1, 0.15 * inch))

    # Footer terms
    story.append(HRFlowable(width="100%", thickness=1, color=SAS_BORDER, spaceAfter=0.08 * inch))
    story.append(Paragraph("<b>Terms & Conditions:</b>", footer_style))
    story.append(Paragraph("1. All equipment must be returned by the agreed return date. Late returns may incur additional charges.", footer_style))
    story.append(Paragraph("2. The client is responsible for any damage, loss, or theft of hired equipment during the rental period.", footer_style))
    story.append(Paragraph("3. Equipment must be returned clean and in the same condition as received.", footer_style))
    story.append(Spacer(1, 0.08 * inch))
    footer_center = ParagraphStyle("FooterCenter", parent=footer_style, alignment=TA_CENTER)
    story.append(Paragraph("Generated by SAS Management System - SAS Best Foods Equipment Hire", footer_center))

    # Build with watermark
    try:
        from sas_management.utils.reportlab_watermark import make_center_watermark_callback
        wm = make_center_watermark_callback(static_folder=current_app.static_folder, opacity=0.08, width_ratio=0.35)
        doc.build(story, onFirstPage=wm, onLaterPages=wm)
    except Exception:
        doc.build(story)

    return buf.getvalue()
