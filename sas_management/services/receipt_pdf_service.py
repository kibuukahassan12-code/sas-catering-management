"""Receipt PDF generation (shared for Invoice & Accounting receipts)."""

from __future__ import annotations

import os
from datetime import date as date_type
from decimal import Decimal
from io import BytesIO
from typing import Optional, Tuple

from flask import current_app, has_app_context


def _ensure_reportlab() -> bool:
    """Ensure ReportLab is importable (auto-installs if needed)."""
    try:
        from sas_management.utils.pdf_dependencies import ensure_reportlab_installed

        logger = current_app.logger if has_app_context() else None
        return bool(ensure_reportlab_installed(logger=logger))
    except Exception:
        return False


def _invoice_totals(invoice) -> Tuple[Decimal, Decimal]:
    """
    Compute (total, discount) for an invoice consistent with invoice/quotation logic:
    total = max(qty*unit_price - discount, 0), no VAT.
    """
    from decimal import Decimal as D

    event = getattr(invoice, "event", None)
    qty = int(getattr(event, "guest_count", 0) or 0) if event else 0
    if qty <= 0:
        qty = 1

    unit_price = D("0")
    try:
        pkg = getattr(event, "menu_package_obj", None) if event else None
        if pkg is not None and getattr(pkg, "price_per_guest", None):
            unit_price = D(str(pkg.price_per_guest))
        else:
            # fallback from invoice stored total
            unit_price = D(str(getattr(invoice, "total_amount_ugx", 0) or 0)) / D(str(qty))
    except Exception:
        unit_price = D("0")

    try:
        discount = D(str(getattr(event, "budget_estimate", 0) or 0)) if event else D("0")
    except Exception:
        discount = D("0")
    if discount < 0:
        discount = D("0")

    subtotal_gross = unit_price * D(str(qty))
    total = subtotal_gross - discount
    if total < 0:
        total = D("0")
    return total, discount


def generate_invoice_receipt_pdf_bytes(receipt, invoice) -> bytes:
    """Generate a PDF for an invoice Receipt (branded invoice-style layout)."""
    if not _ensure_reportlab():
        raise ImportError("PDF engine unavailable")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
    from reportlab.lib.enums import TA_CENTER

    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")

    event = getattr(invoice, "event", None)
    client = getattr(event, "client", None) if event else None

    receipt_no = getattr(receipt, "receipt_number", "") or ""
    pay_date = getattr(receipt, "payment_date", None)
    method = getattr(receipt, "payment_method", "") or ""
    amount = Decimal(str(getattr(receipt, "amount_received_ugx", 0) or 0))

    total, discount = _invoice_totals(invoice)
    # sum all receipts on invoice
    try:
        paid_total = sum(Decimal(str(r.amount_received_ugx or 0)) for r in (invoice.receipts or []))
    except Exception:
        paid_total = amount
    balance = total - paid_total
    if balance < 0:
        balance = Decimal("0")

    def money(v: Decimal) -> str:
        return f"{CURRENCY}{v:,.2f}"

    # SAS Brand Colors (match invoice_service)
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
    )
    styles = getSampleStyleSheet()

    # Header (logo left, company info right) - same structure as invoice PDF
    logo_img = None
    try:
        for fn in ("sas_logo.png", "ssas_logo.png"):
            logo_path = os.path.join(current_app.static_folder or "", "images", fn)
            if os.path.exists(logo_path):
                logo_img = Image(logo_path, width=1.2 * inch, height=1.2 * inch)
                break
    except Exception:
        logo_img = None

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

    story = [header_table, Spacer(1, 0.25 * inch)]

    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Normal"],
        fontSize=20,
        textColor=SAS_ORANGE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    story.append(Paragraph("RECEIPT", title_style))
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

    inv_no = getattr(invoice, "invoice_number", "") or ""

    left_data = []
    left_data.append([Paragraph("RECEIPT DETAILS", section_title_style), ""])
    left_data.append([Paragraph("Receipt Number:", label_style), Paragraph(receipt_no or "N/A", value_style)])
    left_data.append([Paragraph("Payment Date:", label_style), Paragraph(pay_date.strftime("%B %d, %Y") if pay_date else "N/A", value_style)])
    left_data.append([Paragraph("Method:", label_style), Paragraph(method or "N/A", value_style)])
    left_data.append([Paragraph("Invoice #:", label_style), Paragraph(inv_no or "N/A", value_style)])
    left_data.append([Paragraph("Balance Due:", label_style), Paragraph(money(balance), value_style)])
    left_data.append(["", ""])

    amount_text = Paragraph(money(amount), amount_style)
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
    left_data.append(["", ""])

    right_data = []
    if client:
        right_data.append([Paragraph("BILL TO", section_title_style), ""])
        # Name - client's name
        right_data.append([Paragraph("Name:", label_style), Paragraph(getattr(client, "name", None) or "N/A", value_style)])
        # Phone - client's phone number
        ph = getattr(client, "phone", None)
        if ph:
            right_data.append([Paragraph("Phone:", label_style), Paragraph(str(ph), value_style)])
        # Email
        em = getattr(client, "email", None)
        if em:
            right_data.append([Paragraph("Email:", label_style), Paragraph(str(em), value_style)])
        # Address - use client address, or event venue if not provided
        addr = getattr(client, "address", None)
        if not addr and event:
            addr = getattr(event, "venue", None)
        if addr:
            right_data.append([Paragraph("Address:", label_style), Paragraph(str(addr), value_style)])
        right_data.append(["", ""])

    if event:
        right_data.append([Paragraph("EVENT DETAILS", section_title_style), ""])
        ev_name = getattr(event, "event_name", None) or getattr(event, "title", None) or "N/A"
        right_data.append([Paragraph("Event Name:", label_style), Paragraph(str(ev_name), value_style)])
        ev_date = getattr(event, "event_date", None) or getattr(event, "date", None)
        if ev_date:
            right_data.append([Paragraph("Event Date:", label_style), Paragraph(ev_date.strftime("%B %d, %Y"), value_style)])
        gc = getattr(event, "guest_count", None)
        if gc:
            right_data.append([Paragraph("Guests:", label_style), Paragraph(str(gc), value_style)])
        venue = getattr(event, "venue", None)
        if venue:
            right_data.append([Paragraph("Venue:", label_style), Paragraph(str(venue), value_style)])

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
    main_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(main_table)
    story.append(Spacer(1, 0.25 * inch))

    story.append(HRFlowable(width="100%", thickness=1, color=SAS_BORDER, spaceAfter=0.15 * inch))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=SAS_DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    story.append(Paragraph("This receipt confirms payment has been received. Thank you!", footer_style))
    story.append(Paragraph("SAS Best Foods - Catering & Event Management", footer_style))

    from sas_management.utils.reportlab_watermark import make_center_watermark_callback
    wm = make_center_watermark_callback(static_folder=current_app.static_folder, opacity=0.12, width_ratio=0.40)
    doc.build(story, onFirstPage=wm, onLaterPages=wm)
    return buf.getvalue()


def _safe_filename_part(value: str) -> str:
    """Make a user/model value safe for a filename part."""
    v = (value or "").strip()
    if not v:
        return ""
    for ch in ("/", "\\", ":", "*", "?", "\"", "<", ">", "|"):
        v = v.replace(ch, "_")
    return v


def generate_invoice_receipt_pdf(receipt, invoice) -> str:
    """Generate (and save) an invoice receipt PDF and return the full file path."""
    pdf_bytes = generate_invoice_receipt_pdf_bytes(receipt, invoice)

    out_dir = os.path.join(current_app.instance_path, "receipts")
    os.makedirs(out_dir, exist_ok=True)

    receipt_no = (
        getattr(receipt, "receipt_number", None)
        or getattr(receipt, "reference", None)
        or str(getattr(receipt, "id", "") or "")
    )
    receipt_no = _safe_filename_part(str(receipt_no))
    if not receipt_no:
        receipt_no = "receipt"

    full_path = os.path.abspath(os.path.join(out_dir, f"receipt_{receipt_no}.pdf"))
    with open(full_path, "wb") as f:
        f.write(pdf_bytes)
    return full_path


def generate_accounting_receipt_pdf_bytes(receipt, payment=None, invoice=None, client=None) -> bytes:
    """Generate a PDF for an AccountingReceipt (models.AccountingReceipt)."""
    if not _ensure_reportlab():
        raise ImportError("PDF engine unavailable")

    # Reuse invoice receipt layout if linked to invoice
    if invoice is not None and payment is not None:
        # Create a lightweight adapter object for the function above
        class _Tmp:
            receipt_number = getattr(receipt, "reference", "")
            payment_date = getattr(receipt, "date", None) or getattr(payment, "date", None) or date_type.today()
            payment_method = getattr(receipt, "method", None) or getattr(payment, "method", None) or "Cash"
            amount_received_ugx = getattr(receipt, "amount", None) or getattr(payment, "amount", None) or 0

        return generate_invoice_receipt_pdf_bytes(_Tmp(), invoice)

    # Otherwise generate a generic receipt
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT

    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")

    receipt_no = getattr(receipt, "reference", "") or ""
    pay_date = getattr(receipt, "date", None)
    method = getattr(receipt, "method", "") or ""
    amount = Decimal(str(getattr(receipt, "amount", 0) or 0))

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=0.6 * inch, rightMargin=0.6 * inch, topMargin=0.5 * inch, bottomMargin=0.4 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=18, alignment=TA_LEFT)
    small = ParagraphStyle("S", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#444444"), leading=11)
    label = ParagraphStyle("L", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#222222"))
    right = ParagraphStyle("R", parent=styles["Normal"], fontSize=9, alignment=TA_RIGHT)

    story = []
    story.append(Paragraph("PAYMENT RECEIPT", title_style))
    story.append(Paragraph("SAS Best Foods", ParagraphStyle("H", parent=styles["Normal"], fontName="Helvetica-Bold")))
    story.append(Paragraph("Tel: 0702060778 / 0745705088 · Website: www.sasbestfoods.com", small))
    story.append(Spacer(1, 10))

    meta = [
        [Paragraph("<b>Receipt #</b>", label), Paragraph(receipt_no, right)],
        [Paragraph("<b>Date</b>", label), Paragraph(pay_date.strftime("%b %d, %Y") if pay_date else "N/A", right)],
        [Paragraph("<b>Method</b>", label), Paragraph(method or "N/A", right)],
    ]
    meta_t = Table(meta, colWidths=[2.0 * inch, 4.2 * inch])
    meta_t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5d5d5"))]))
    story.append(meta_t)
    story.append(Spacer(1, 10))

    payer = getattr(client, "name", None) if client else None
    story.append(Paragraph(f"<b>Received From:</b> {payer or 'Client'}", small))
    story.append(Spacer(1, 10))

    items = [["Description", "Amount"], ["Payment received", f"{CURRENCY}{amount:,.2f}"]]
    items_t = Table(items, colWidths=[4.6 * inch, 1.6 * inch])
    items_t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efefef")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d5d5d5")), ("ALIGN", (1, 1), (1, -1), "RIGHT")]))
    story.append(items_t)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Generated by SAS Management System · SAS Best Foods", small))

    from sas_management.utils.reportlab_watermark import make_center_watermark_callback
    wm = make_center_watermark_callback(static_folder=current_app.static_folder, opacity=0.12, width_ratio=0.40)
    doc.build(story, onFirstPage=wm, onLaterPages=wm)
    return buf.getvalue()

