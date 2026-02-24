"""Unified PDF generation for Quotation/Invoice/Receipt (ReportLab)."""

from __future__ import annotations

import os
from decimal import Decimal
from io import BytesIO
from typing import Any, Optional, Tuple

from flask import current_app, has_app_context


def _ensure_reportlab() -> bool:
    try:
        from sas_management.utils.pdf_dependencies import ensure_reportlab_installed

        logger = current_app.logger if has_app_context() else None
        return bool(ensure_reportlab_installed(logger=logger))
    except Exception:
        return False


def _load_logo_path() -> Optional[str]:
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


def _calc_unit_price_and_qty(event: Any) -> Tuple[Decimal, int, str, str]:
    qty = int(getattr(event, "guest_count", 0) or 0)
    if qty <= 0:
        qty = 1
    pkg = getattr(event, "menu_package_obj", None)
    pkg_name = "Catering Package"
    pkg_desc = ""
    unit = Decimal("0")
    try:
        if pkg is not None and getattr(pkg, "price_per_guest", None):
            unit = Decimal(str(pkg.price_per_guest))
            pkg_name = f"{getattr(pkg, 'name', 'Catering')} Package"
            pkg_desc = getattr(pkg, "description", "") or f"Package for {qty} guests"
    except Exception:
        unit = Decimal("0")
    return unit, qty, pkg_name, pkg_desc


def _calc_discount(event: Any) -> Decimal:
    try:
        d = Decimal(str(getattr(event, "budget_estimate", 0) or 0))
    except Exception:
        d = Decimal("0")
    if d < 0:
        d = Decimal("0")
    return d


def _money(x) -> Decimal:
    try:
        return Decimal(str(x or 0))
    except Exception:
        return Decimal("0")


def _build_doc(title: str):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.4 * inch,
        title=title,
    )
    return doc, buf


def _styles():
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT

    s = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=18, alignment=TA_LEFT, spaceAfter=10)
    brand = ParagraphStyle("Brand", parent=s["Normal"], fontName="Helvetica-Bold", fontSize=14, spaceAfter=2, textColor=colors.HexColor("#111111"))
    meta = ParagraphStyle("Meta", parent=s["Normal"], fontSize=9.5, textColor=colors.HexColor("#222222"))
    muted = ParagraphStyle("Muted", parent=s["Normal"], fontSize=9.5, textColor=colors.HexColor("#555555"))
    right = ParagraphStyle("Right", parent=s["Normal"], fontSize=9.5, alignment=TA_RIGHT, textColor=colors.HexColor("#222222"))
    return title, brand, meta, muted, right, colors


def generate_invoice_pdf_bytes(invoice) -> bytes:
    """Invoice PDF in the exact SAS reference layout (no VAT)."""
    if not _ensure_reportlab():
        raise ImportError("PDF engine unavailable")

    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image

    title_s, brand_s, meta_s, muted_s, right_s, colors = _styles()
    doc, buf = _build_doc(f"Invoice {getattr(invoice, 'invoice_number', '')}")

    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")

    event = getattr(invoice, "event", None)
    client = getattr(event, "client", None) if event else None

    unit, qty, pkg_name, pkg_desc = _calc_unit_price_and_qty(event) if event else (Decimal("0"), 1, "Catering Package", "")
    discount = _calc_discount(event) if event else Decimal("0")
    subtotal_gross = unit * Decimal(str(qty))
    total = subtotal_gross - discount
    if total < 0:
        total = Decimal("0")

    try:
        amount_paid = sum(_money(r.amount_received_ugx) for r in (invoice.receipts or []))
    except Exception:
        amount_paid = Decimal("0")
    balance_due = total - amount_paid
    if balance_due < 0:
        balance_due = Decimal("0")

    inv_no = getattr(invoice, "invoice_number", "") or ""
    issue_date = getattr(invoice, "issue_date", None)
    due_date = getattr(invoice, "due_date", None)
    status = (
        getattr(getattr(invoice, "status", None), "value", None)
        or getattr(invoice, "status", None)
        or "N/A"
    )

    def money(amount: Decimal) -> str:
        return f"{CURRENCY}{amount:,.2f}"

    BORDER = colors.HexColor("#b9b9b9")
    GRID = colors.HexColor("#d5d5d5")
    HEADER_BG = colors.HexColor("#efefef")
    TEXT = colors.HexColor("#111111")
    MUTED = colors.HexColor("#555555")

    # --- Styles tuned to match reference image ---
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle

    title_ref = ParagraphStyle(
        "TitleRef",
        parent=title_s,
        fontSize=16.5,
        textColor=TEXT,
        spaceAfter=6,
    )
    company_name = ParagraphStyle(
        "CompanyName",
        parent=brand_s,
        fontSize=12.5,
        textColor=TEXT,
        spaceAfter=2,
    )
    small_ref = ParagraphStyle("SmallRef", parent=muted_s, fontSize=8.7, leading=10.4, textColor=MUTED)
    meta_label = ParagraphStyle("MetaLabel", parent=meta_s, fontSize=8.7, textColor=TEXT)
    meta_value = ParagraphStyle("MetaValue", parent=right_s, fontSize=8.7, textColor=TEXT)
    meta_total_label = ParagraphStyle("MetaTotalLabel", parent=meta_s, fontName="Helvetica-Bold", fontSize=10.5, textColor=TEXT)
    meta_total_value = ParagraphStyle("MetaTotalValue", parent=right_s, fontName="Helvetica-Bold", fontSize=10.5, textColor=TEXT)

    story = []

    # Header: two columns (left company, right meta box)
    logo_path = _load_logo_path()
    logo = None
    if logo_path:
        try:
            logo = Image(logo_path, width=24, height=24)
        except Exception:
            logo = None

    left_block = [
        Paragraph("CATERING INVOICE", title_ref),
        Table(
            [
                [logo or "", Paragraph("SAS Best Foods", company_name)],
            ],
            colWidths=[0.35 * 72, 3.7 * 72],
        ),
        Paragraph("Near Akamwesi Mall, Gayaza Rd, Opp Electoral Commission Kawempe Offices", small_ref),
        Paragraph("Kawempe, Kampala, Uganda", small_ref),
        Paragraph("Tel: 0702060778 / 0745705088", small_ref),
        Paragraph("Email: info@sasbestfoods.com | Website: www.sasbestfoods.com", small_ref),
    ]

    meta_rows = [
        ("Invoice #", inv_no),
        ("Issue Date", issue_date.strftime("%b %d, %Y") if issue_date else "N/A"),
        ("Due Date", due_date.strftime("%b %d, %Y") if due_date else "N/A"),
        ("Status", str(status)),
        ("Discount", f"-{money(discount)}" if discount > 0 else f"-{CURRENCY}0.00"),
        ("Amount Paid", money(amount_paid)),
        ("Balance Due", money(balance_due)),
    ]
    meta_tbl = Table(
        [[Paragraph(f"<b>{k}</b>", meta_label), Paragraph(v, meta_value)] for k, v in meta_rows]
        + [[Paragraph("TOTAL", meta_total_label), Paragraph(money(total), meta_total_value)]],
        colWidths=[1.4 * 72, 1.55 * 72],
    )
    meta_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("INNERGRID", (0, 0), (-1, -2), 0, colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEABOVE", (0, -1), (-1, -1), 1, BORDER),
                ("TOPPADDING", (0, -1), (-1, -1), 7),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
            ]
        )
    )

    header_tbl = Table([[left_block, meta_tbl]], colWidths=[4.25 * 72, 2.95 * 72])
    header_tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header_tbl)
    story.append(Spacer(1, 10))

    bill_left = []
    if client:
        bill_left.append(Paragraph(f"<b>{getattr(client, 'name', None) or 'Client'}</b>", meta_s))
        for f in ("contact_person", "phone", "email"):
            val = getattr(client, f, None)
            if val:
                bill_left.append(Paragraph(str(val), muted_s))
    else:
        bill_left.append(Paragraph("No client information available", muted_s))

    bill_right = []
    if event:
        bill_right.append(Paragraph(f"<b>{getattr(event, 'title', None) or 'Event'}</b>", meta_s))
        d = getattr(event, "date", None) or getattr(event, "event_date", None)
        bill_right.append(Paragraph(d.strftime("%b %d, %Y") if d else "No Date", muted_s))
        gc = getattr(event, "guest_count", None)
        if gc:
            bill_right.append(Paragraph(f"{gc} guests", muted_s))
    else:
        bill_right.append(Paragraph("No event linked", muted_s))

    # BILL TO / EVENT boxes
    box_hdr = ParagraphStyle("BoxHdr", parent=meta_s, fontName="Helvetica-Bold", fontSize=9, textColor=TEXT)
    bill_tbl = Table(
        [
            [Paragraph("BILL TO", box_hdr), Paragraph("EVENT", box_hdr)],
            [bill_left, bill_right],
        ],
        colWidths=[3.55 * 72, 3.55 * 72],
    )
    bill_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (0, 1), 1, BORDER),
                ("BOX", (1, 0), (1, 1), 1, BORDER),
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("TOPPADDING", (0, 1), (-1, 1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )
    story.append(bill_tbl)
    story.append(Spacer(1, 10))

    # Items table (boxed, header row)
    th = ParagraphStyle("Th", parent=meta_s, fontName="Helvetica-Bold", fontSize=8.7, textColor=TEXT)
    td = ParagraphStyle("Td", parent=meta_s, fontSize=8.7, textColor=TEXT)
    td_muted = ParagraphStyle("TdMuted", parent=muted_s, fontSize=8.2, leading=10.0, textColor=MUTED)

    desc_cell = [
        Paragraph(f"<b>{pkg_name}</b>", td),
        Paragraph(pkg_desc or "", td_muted),
    ]
    items = [
        [Paragraph("DESCRIPTION", th), Paragraph("QTY", th), Paragraph("UNIT PRICE", th), Paragraph("AMOUNT", th)],
        [desc_cell, Paragraph(str(qty), td), Paragraph(money(unit), td), Paragraph(money(subtotal_gross), td)],
    ]
    items_tbl = Table(items, colWidths=[3.7 * 72, 0.6 * 72, 1.05 * 72, 1.05 * 72])
    items_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GRID),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                ("TOPPADDING", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
            ]
        )
    )
    story.append(items_tbl)
    story.append(Spacer(1, 10))

    # Bottom: notes box (left) + totals box (right)
    notes_hdr = ParagraphStyle("NotesHdr", parent=meta_s, fontName="Helvetica-Bold", fontSize=9, textColor=TEXT)
    notes_body = ParagraphStyle("NotesBody", parent=muted_s, fontSize=8.5, leading=10.5, textColor=MUTED)
    notes_box = Table(
        [
            [Paragraph("NOTES / TERMS", notes_hdr)],
            [Paragraph("Payment terms: 30 days from invoice date. Thank you for your business.", notes_body)],
        ],
        colWidths=[3.55 * 72],
    )
    notes_box.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 1), (-1, 1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )

    totals_rows = [
        ("Subtotal", money(subtotal_gross)),
        ("Discount", f"-{money(discount)}" if discount > 0 else f"-{CURRENCY}0.00"),
        ("Total", money(total)),
        ("Amount Paid", money(amount_paid)),
        ("Balance Due", money(balance_due)),
    ]
    totals_tbl = Table(
        [[Paragraph(k, meta_label), Paragraph(v, meta_value)] for k, v in totals_rows[:2]]
        + [[Paragraph("<b>Total</b>", meta_label), Paragraph(f"<b>{totals_rows[2][1]}</b>", meta_value)]]
        + [[Paragraph(k, meta_label), Paragraph(v, meta_value)] for k, v in totals_rows[3:4]]
        + [[Paragraph("<b>Balance Due</b>", meta_label), Paragraph(f"<b>{totals_rows[4][1]}</b>", meta_value)]],
        colWidths=[1.65 * 72, 1.9 * 72],
    )
    totals_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, 2), (-1, 2), 0.5, GRID),  # above Total
                ("LINEABOVE", (0, -1), (-1, -1), 0.5, GRID),  # above Balance Due
            ]
        )
    )

    bottom_tbl = Table([[notes_box, totals_tbl]], colWidths=[3.55 * 72, 3.55 * 72])
    bottom_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(bottom_tbl)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Generated by SAS Management System · SAS Best Foods", ParagraphStyle("Footer", parent=muted_s, fontSize=8.2, alignment=TA_CENTER)))

    from sas_management.utils.reportlab_watermark import make_center_watermark_callback
    wm = make_center_watermark_callback(static_folder=current_app.static_folder, opacity=0.12, width_ratio=0.40)
    doc.build(story, onFirstPage=wm, onLaterPages=wm)
    return buf.getvalue()


def generate_quotation_pdf_bytes(quotation) -> bytes:
    """Quotation PDF in the exact SAS reference layout (no VAT)."""
    if not _ensure_reportlab():
        raise ImportError("PDF engine unavailable")

    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image

    title_s, brand_s, meta_s, muted_s, right_s, colors = _styles()
    doc, buf = _build_doc(f"Quotation {getattr(quotation, 'id', '')}")
    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")

    event = getattr(quotation, "event", None)
    client = getattr(quotation, "client", None) or (getattr(event, "client", None) if event else None)

    unit, qty, pkg_name, pkg_desc = _calc_unit_price_and_qty(event) if event else (Decimal("0"), 1, "Catering Package", "")
    discount = _calc_discount(event) if event else Decimal("0")
    subtotal_gross = unit * Decimal(str(qty))
    total = subtotal_gross - discount
    if total < 0:
        total = Decimal("0")

    quote_no = str(getattr(quotation, "id", "") or "")
    qd = getattr(quotation, "quote_date", None)
    ed = getattr(quotation, "expiry_date", None)
    status = "Active"

    def money(amount: Decimal) -> str:
        return f"{CURRENCY}{amount:,.2f}"

    BORDER = colors.HexColor("#b9b9b9")
    GRID = colors.HexColor("#d5d5d5")
    HEADER_BG = colors.HexColor("#efefef")
    TEXT = colors.HexColor("#111111")
    MUTED = colors.HexColor("#555555")

    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle

    title_ref = ParagraphStyle("TitleRefQ", parent=title_s, fontSize=16.5, textColor=TEXT, spaceAfter=6)
    company_name = ParagraphStyle("CompanyNameQ", parent=brand_s, fontSize=12.5, textColor=TEXT, spaceAfter=2)
    small_ref = ParagraphStyle("SmallRefQ", parent=muted_s, fontSize=8.7, leading=10.4, textColor=MUTED)
    meta_label = ParagraphStyle("MetaLabelQ", parent=meta_s, fontSize=8.7, textColor=TEXT)
    meta_value = ParagraphStyle("MetaValueQ", parent=right_s, fontSize=8.7, textColor=TEXT)
    meta_total_label = ParagraphStyle("MetaTotalLabelQ", parent=meta_s, fontName="Helvetica-Bold", fontSize=10.5, textColor=TEXT)
    meta_total_value = ParagraphStyle("MetaTotalValueQ", parent=right_s, fontName="Helvetica-Bold", fontSize=10.5, textColor=TEXT)

    story = []

    logo_path = _load_logo_path()
    logo = None
    if logo_path:
        try:
            logo = Image(logo_path, width=24, height=24)
        except Exception:
            logo = None

    left_block = [
        Paragraph("CATERING QUOTATION", title_ref),
        Table([[logo or "", Paragraph("SAS Best Foods", company_name)]], colWidths=[0.35 * 72, 3.7 * 72]),
        Paragraph("Near Akamwesi Mall, Gayaza Rd, Opp Electoral Commission Kawempe Offices", small_ref),
        Paragraph("Kawempe, Kampala, Uganda", small_ref),
        Paragraph("Tel: 0702060778 / 0745705088", small_ref),
        Paragraph("Email: info@sasbestfoods.com | Website: www.sasbestfoods.com", small_ref),
    ]

    meta_rows = [
        ("Quote #", quote_no),
        ("Quote Date", qd.strftime("%b %d, %Y") if qd else "N/A"),
        ("Valid Until", ed.strftime("%b %d, %Y") if ed else "N/A"),
        ("Status", status),
    ]
    meta_tbl = Table(
        [[Paragraph(f"<b>{k}</b>", meta_label), Paragraph(v, meta_value)] for k, v in meta_rows]
        + [[Paragraph("TOTAL", meta_total_label), Paragraph(money(total), meta_total_value)]],
        colWidths=[1.4 * 72, 1.55 * 72],
    )
    meta_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("INNERGRID", (0, 0), (-1, -2), 0, colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEABOVE", (0, -1), (-1, -1), 1, BORDER),
                ("TOPPADDING", (0, -1), (-1, -1), 7),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
            ]
        )
    )

    header_tbl = Table([[left_block, meta_tbl]], colWidths=[4.25 * 72, 2.95 * 72])
    header_tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, 0), 1, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(header_tbl)
    story.append(Spacer(1, 10))

    bill_left = []
    if client:
        bill_left.append(Paragraph(f"<b>{getattr(client, 'name', None) or 'Client'}</b>", meta_s))
        for f in ("contact_person", "phone", "email"):
            val = getattr(client, f, None)
            if val:
                bill_left.append(Paragraph(str(val), muted_s))
    else:
        bill_left.append(Paragraph("No client information available", muted_s))

    bill_right = []
    if event:
        bill_right.append(Paragraph(f"<b>{getattr(event, 'title', None) or 'Event'}</b>", meta_s))
        d = getattr(event, "date", None) or getattr(event, "event_date", None)
        bill_right.append(Paragraph(d.strftime("%b %d, %Y") if d else "No Date", muted_s))
        gc = getattr(event, "guest_count", None)
        if gc:
            bill_right.append(Paragraph(f"{gc} guests", muted_s))
    else:
        bill_right.append(Paragraph("No event linked", muted_s))

    box_hdr = ParagraphStyle("BoxHdrQ", parent=meta_s, fontName="Helvetica-Bold", fontSize=9, textColor=TEXT)
    bill_tbl = Table(
        [[Paragraph("PREPARED FOR", box_hdr), Paragraph("EVENT", box_hdr)], [bill_left, bill_right]],
        colWidths=[3.55 * 72, 3.55 * 72],
    )
    bill_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (0, 1), 1, BORDER),
                ("BOX", (1, 0), (1, 1), 1, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                ("TOPPADDING", (0, 1), (-1, 1), 6),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )
    story.append(bill_tbl)
    story.append(Spacer(1, 10))

    th = ParagraphStyle("ThQ", parent=meta_s, fontName="Helvetica-Bold", fontSize=8.7, textColor=TEXT)
    td = ParagraphStyle("TdQ", parent=meta_s, fontSize=8.7, textColor=TEXT)
    td_muted = ParagraphStyle("TdMutedQ", parent=muted_s, fontSize=8.2, leading=10.0, textColor=MUTED)
    desc_cell = [Paragraph(f"<b>{pkg_name}</b>", td), Paragraph(pkg_desc or "", td_muted)]

    items = [
        [Paragraph("DESCRIPTION", th), Paragraph("QTY", th), Paragraph("UNIT PRICE", th), Paragraph("AMOUNT", th)],
        [desc_cell, Paragraph(str(qty), td), Paragraph(money(unit), td), Paragraph(money(subtotal_gross), td)],
    ]
    items_tbl = Table(items, colWidths=[3.7 * 72, 0.6 * 72, 1.05 * 72, 1.05 * 72])
    items_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GRID),
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
                ("TOPPADDING", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
            ]
        )
    )
    story.append(items_tbl)
    story.append(Spacer(1, 10))

    notes_hdr = ParagraphStyle("NotesHdrQ", parent=meta_s, fontName="Helvetica-Bold", fontSize=9, textColor=TEXT)
    notes_body = ParagraphStyle("NotesBodyQ", parent=muted_s, fontSize=8.5, leading=10.5, textColor=MUTED)
    notes_box = Table(
        [[Paragraph("NOTES / TERMS", notes_hdr)], [Paragraph("Payment terms: 14 days from quotation date. Please confirm acceptance before expiry.", notes_body)]],
        colWidths=[3.55 * 72],
    )
    notes_box.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 1), (-1, 1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ]
        )
    )

    totals_rows = [
        ("Subtotal", money(subtotal_gross)),
        ("Discount", f"-{money(discount)}" if discount > 0 else f"-{CURRENCY}0.00"),
        ("Total", money(total)),
    ]
    totals_tbl = Table(
        [[Paragraph(k, meta_label), Paragraph(v, meta_value)] for k, v in totals_rows[:2]]
        + [[Paragraph("<b>Total</b>", meta_label), Paragraph(f"<b>{totals_rows[2][1]}</b>", meta_value)]],
        colWidths=[1.65 * 72, 1.9 * 72],
    )
    totals_tbl.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, 2), (-1, 2), 0.5, GRID),
            ]
        )
    )

    bottom_tbl = Table([[notes_box, totals_tbl]], colWidths=[3.55 * 72, 3.55 * 72])
    bottom_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(bottom_tbl)
    story.append(Spacer(1, 10))
    story.append(Paragraph("Generated by SAS Management System · SAS Best Foods", ParagraphStyle("FooterQ", parent=muted_s, fontSize=8.2, alignment=TA_CENTER)))

    from sas_management.utils.reportlab_watermark import make_center_watermark_callback
    wm = make_center_watermark_callback(static_folder=current_app.static_folder, opacity=0.12, width_ratio=0.40)
    doc.build(story, onFirstPage=wm, onLaterPages=wm)
    return buf.getvalue()

