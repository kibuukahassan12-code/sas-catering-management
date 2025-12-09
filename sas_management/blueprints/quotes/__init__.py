from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from models import (
    BakeryItem,
    Client,
    Event,
    Invoice,
    InvoiceStatus,
    Quotation,
    QuotationLine,
    QuotationSource,
    UserRole,
    db,
)
# from modules.catering_menu import CATERING_MENU
from utils import role_required, paginate_query
from utils.helpers import parse_date

quotes_bp = Blueprint("quotes", __name__, url_prefix="/quotes")

def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def _generate_invoice_number():
    """Generate a unique invoice number."""
    from models import Invoice
    today = date.today()
    prefix = f"INV-{today.strftime('%Y%m%d')}"
    last_invoice = (
        Invoice.query.filter(Invoice.invoice_number.like(f"{prefix}%"))
        .order_by(Invoice.invoice_number.desc())
        .first()
    )
    if last_invoice:
        try:
            last_num = int(last_invoice.invoice_number.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    return f"{prefix}-{new_num:04d}"

def _collect_catering_lines():
    # lookup = {item["id"]: item for item in CATERING_MENU}
    lookup = {}  # CATERING_MENU disabled
    ids = request.form.getlist("catering_item_id[]")
    quantities = request.form.getlist("catering_quantity[]")
    lines = []
    for raw_id, raw_qty in zip(ids, quantities):
        if not raw_id:
            continue
        qty = _parse_int(raw_qty) or 0
        if qty <= 0:
            continue
        menu_item = lookup.get(raw_id)
        if not menu_item:
            continue
        unit_price = Decimal(menu_item["unit_price"])
        lines.append(
            {
                "source_type": QuotationSource.Catering,
                "source_reference": raw_id,
                "item_name": menu_item["name"],
                "unit_price": unit_price,
                "quantity": qty,
            }
        )
    return lines

def _collect_bakery_lines(bakery_items):
    lookup = {str(item.id): item for item in bakery_items}
    ids = request.form.getlist("bakery_item_id[]")
    quantities = request.form.getlist("bakery_quantity[]")
    lines = []
    for raw_id, raw_qty in zip(ids, quantities):
        if not raw_id:
            continue
        qty = _parse_int(raw_qty) or 0
        if qty <= 0:
            continue
        bakery_item = lookup.get(raw_id)
        if not bakery_item:
            continue
        # Use the new get_current_price method
        unit_price = Decimal(bakery_item.get_current_price() or 0)
        lines.append(
            {
                "source_type": QuotationSource.Bakery,
                "source_reference": raw_id,
                "item_name": bakery_item.name,
                "unit_price": unit_price,
                "quantity": qty,
            }
        )
    return lines

@quotes_bp.route("")
@quotes_bp.route("/")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def dashboard():
    """Quotations dashboard."""
    # Get filter parameters
    status_filter = request.args.get("status", "")
    client_filter = request.args.get("client_id", type=int)
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    # Build query
    query = Quotation.query.options(
        joinedload(Quotation.client),
        joinedload(Quotation.event)
    )
    
    # Apply filters
    if client_filter:
        query = query.filter(Quotation.client_id == client_filter)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(Quotation.quote_date >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(Quotation.quote_date <= to_date)
        except ValueError:
            pass
    
    # Order by most recent first
    query = query.order_by(Quotation.quote_date.desc(), Quotation.id.desc())
    
    # Paginate
    pagination = paginate_query(query, per_page=20)
    quotations = pagination.items
    
    # Calculate statistics
    total_quotations = Quotation.query.count()
    total_value = db.session.query(func.sum(Quotation.subtotal)).scalar() or Decimal("0.00")
    active_quotations = Quotation.query.filter(Quotation.expiry_date >= date.today()).count()
    expired_quotations = Quotation.query.filter(Quotation.expiry_date < date.today()).count()
    
    # Get all clients for filter
    clients = Client.query.order_by(Client.name.asc()).all()
    
    today = date.today()
    return render_template(
        "quotes/dashboard.html",
        quotations=quotations,
        pagination=pagination,
        clients=clients,
        total_quotations=total_quotations,
        total_value=total_value,
        active_quotations=active_quotations,
        expired_quotations=expired_quotations,
        status_filter=status_filter,
        client_filter=client_filter,
        date_from=date_from,
        date_to=date_to,
        today=today,
    )

@quotes_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def new_quote():
    clients = Client.query.order_by(Client.name.asc()).all()
    # Get all events (not just draft) - event is now optional
    all_events = (
        Event.query
        .order_by(Event.event_date.desc())
        .all()
    )
    bakery_items = (
        BakeryItem.query.filter(BakeryItem.status == "Active")
        .order_by(BakeryItem.name.asc())
        .all()
    )
    default_quote_date = date.today()
    default_expiry = default_quote_date + timedelta(days=14)

    if not clients:
        flash("Add a client record before creating a quote.", "warning")
        return redirect(url_for("core.clients_add"))

    if request.method == "POST":
        client_id = request.form.get("client_id", type=int)
        event_id = request.form.get("event_id", type=int) or None  # Event is now optional
        quote_date = parse_date(request.form.get("quote_date"), default_quote_date)
        expiry_date = parse_date(request.form.get("expiry_date"), default_expiry)

        if not client_id:
            flash("Select a client to build a quote.", "danger")
            return render_template(
                "quotes/new.html",
                clients=clients,
                events=all_events,
                bakery_items=bakery_items,
                catering_menu=[],  # CATERING_MENU disabled
                default_quote_date=default_quote_date,
                default_expiry_date=default_expiry,
            )

        if expiry_date <= quote_date:
            flash("Expiry date must be later than the quote date.", "danger")
            return render_template(
                "quotes/new.html",
                clients=clients,
                events=all_events,
                bakery_items=bakery_items,
                catering_menu=[],  # CATERING_MENU disabled
                default_quote_date=default_quote_date,
                default_expiry_date=default_expiry,
            )

        # If event is provided, validate it belongs to the client
        if event_id:
            selected_event = Event.query.get(event_id)
            if selected_event and selected_event.client_id != client_id:
                flash("The event you selected belongs to a different client.", "danger")
                return render_template(
                    "quotes/new.html",
                    clients=clients,
                    events=all_events,
                    bakery_items=bakery_items,
                    catering_menu=[],  # CATERING_MENU disabled
                    default_quote_date=default_quote_date,
                    default_expiry_date=default_expiry,
                )

        lines = _collect_catering_lines() + _collect_bakery_lines(bakery_items)
        if not lines:
            flash("Add at least one line item to the quote.", "danger")
            return render_template(
                "quotes/new.html",
                clients=clients,
                events=all_events,
                bakery_items=bakery_items,
                catering_menu=[],  # CATERING_MENU disabled
                default_quote_date=default_quote_date,
                default_expiry_date=default_expiry,
            )

        subtotal = Decimal("0.00")
        quotation = Quotation(
            client_id=client_id,
            event_id=event_id,
            quote_date=quote_date,
            expiry_date=expiry_date,
            subtotal=subtotal,
        )
        db.session.add(quotation)
        db.session.flush()

        for payload in lines:
            line_total = payload["unit_price"] * payload["quantity"]
            subtotal += line_total
            db.session.add(
                QuotationLine(
                    quotation_id=quotation.id,
                    source_type=payload["source_type"],
                    source_reference=payload["source_reference"],
                    item_name=payload["item_name"],
                    unit_price=payload["unit_price"],
                    quantity=payload["quantity"],
                    line_total=line_total,
                )
            )

        quotation.subtotal = subtotal
        db.session.commit()
        flash("Quotation created successfully.", "success")
        return redirect(url_for("quotes.view_quote", quotation_id=quotation.id))

    return render_template(
        "quotes/new.html",
        clients=clients,
        events=all_events,
        bakery_items=bakery_items,
        catering_menu=[],  # CATERING_MENU disabled
        default_quote_date=default_quote_date,
        default_expiry_date=default_expiry,
    )

@quotes_bp.route("/view/<int:quotation_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def view_quote(quotation_id):
    quotation = (
        Quotation.query.options(joinedload(Quotation.lines), joinedload(Quotation.client), joinedload(Quotation.event))
        .filter(Quotation.id == quotation_id)
        .first_or_404()
    )
    # Check if invoice already exists for this event
    existing_invoice = None
    if quotation.event_id:
        existing_invoice = Invoice.query.filter_by(event_id=quotation.event_id).first()
    return render_template("quotes/view.html", quotation=quotation, existing_invoice=existing_invoice)

@quotes_bp.route("/convert/<int:quotation_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def convert_to_invoice(quotation_id):
    """Convert a quotation to an invoice."""
    from datetime import timedelta
    from models import InvoiceStatus

    quotation = (
        Quotation.query.options(joinedload(Quotation.event))
        .filter(Quotation.id == quotation_id)
        .first_or_404()
    )

    if not quotation.event_id:
        flash("Cannot convert quote to invoice: quote is not linked to an event.", "danger")
        return redirect(url_for("quotes.view_quote", quotation_id=quotation_id))

    # Check if invoice already exists
    existing_invoice = Invoice.query.filter_by(event_id=quotation.event_id).first()
    if existing_invoice:
        flash(f"Invoice already exists for this event: {existing_invoice.invoice_number}", "warning")
        return redirect(url_for("invoices.invoice_view", invoice_id=existing_invoice.id))

    # Create invoice
    invoice = Invoice(
        event_id=quotation.event_id,
        invoice_number=_generate_invoice_number(),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),  # 30 days payment terms
        total_amount_ugx=quotation.subtotal,
        status=InvoiceStatus.Issued,
    )
    db.session.add(invoice)
    db.session.commit()

    flash(f"Invoice {invoice.invoice_number} created successfully from quote.", "success")
    return redirect(url_for("invoices.invoice_view", invoice_id=invoice.id))

