from datetime import date, datetime, timedelta
from decimal import Decimal
import os

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for, current_app
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from sas_management.models import (
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
from sas_management.utils import role_required, paginate_query
from sas_management.utils.helpers import parse_date

quotes_bp = Blueprint("quotes", __name__, url_prefix="/quotes")

def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

def _generate_invoice_number():
    """Generate a unique invoice number."""
    from sas_management.models import Invoice
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
    
    # Calculate statistics - handle NULL values safely
    total_quotations = Quotation.query.count()
    total_value_result = db.session.query(func.sum(Quotation.subtotal)).scalar()
    total_value = Decimal(str(total_value_result)) if total_value_result is not None else Decimal("0.00")
    
    today = date.today()
    active_quotations = Quotation.query.filter(
        Quotation.expiry_date.isnot(None),
        Quotation.expiry_date >= today
    ).count()
    expired_quotations = Quotation.query.filter(
        Quotation.expiry_date.isnot(None),
        Quotation.expiry_date < today
    ).count()
    
    # Get all clients for filter
    clients = Client.query.order_by(Client.name.asc()).all()
    
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

@quotes_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def create_quote():
    """Create a new quotation with custom line items."""
    clients = Client.query.order_by(Client.name.asc()).all()
    default_quote_date = date.today()
    default_expiry = default_quote_date + timedelta(days=14)
    
    if request.method == "POST":
        try:
            # Get form data
            client_id = request.form.get("client_id", type=int)
            title = request.form.get("title", "").strip()
            event_type = request.form.get("event_type", "").strip()
            event_date_str = request.form.get("event_date")
            quote_date = parse_date(request.form.get("quote_date"), default_quote_date)
            expiry_date = parse_date(request.form.get("expiry_date"), default_expiry)
            tax_rate = Decimal(str(request.form.get("tax_rate", 0) or 0))
            
            # Handle new client creation
            if not client_id:
                # Check if new client details were provided
                client_name = request.form.get("client_name", "").strip()
                contact_person = request.form.get("contact_person", "").strip()
                client_phone = request.form.get("client_phone", "").strip()
                client_email = request.form.get("client_email", "").strip()
                client_company = request.form.get("client_company", "").strip()
                client_address = request.form.get("client_address", "").strip()
                
                if client_name and contact_person and client_phone and client_email:
                    # Create new client
                    # Check if client with same email already exists
                    existing_client = Client.query.filter_by(email=client_email).first()
                    if existing_client:
                        client_id = existing_client.id
                        flash(f"Client with email {client_email} already exists. Using existing client record.", "info")
                    else:
                        new_client = Client(
                            name=client_name,
                            contact_person=contact_person,
                            phone=client_phone,
                            email=client_email,
                            company=client_company if client_company else None,
                            address=client_address if client_address else None
                        )
                        db.session.add(new_client)
                        db.session.flush()
                        client_id = new_client.id
                        db.session.commit()  # Commit client creation before proceeding
                        flash(f"New client '{client_name}' created successfully!", "success")
                else:
                    flash("Please either select an existing client or provide all required client details (Name, Contact Person, Phone, Email).", "danger")
                    return render_template(
                        "quotes/quotation_new.html",
                        clients=clients,
                        default_quote_date=default_quote_date.isoformat(),
                        default_expiry_date=default_expiry.isoformat(),
                    )
            
            # Validation
            if not client_id:
                flash("Please select a client or provide client details.", "danger")
                return render_template(
                    "quotes/quotation_new.html",
                    clients=clients,
                    default_quote_date=default_quote_date.isoformat(),
                    default_expiry_date=default_expiry.isoformat(),
                )
            
            if expiry_date <= quote_date:
                flash("Expiry date must be later than the quote date.", "danger")
                return render_template(
                    "quotes/quotation_new.html",
                    clients=clients,
                    default_quote_date=default_quote_date.isoformat(),
                    default_expiry_date=default_expiry.isoformat(),
                )
            
            # Parse event date
            event_date = None
            if event_date_str:
                try:
                    event_date = parse_date(event_date_str, None)
                except:
                    pass
            
            # Get line items
            item_names = request.form.getlist("item_name[]")
            item_descriptions = request.form.getlist("item_description[]")
            item_quantities = request.form.getlist("item_quantity[]")
            item_unit_prices = request.form.getlist("item_unit_price[]")
            
            # Validate line items
            line_items = []
            for i in range(len(item_names)):
                name = item_names[i].strip() if i < len(item_names) else ""
                description = item_descriptions[i].strip() if i < len(item_descriptions) else ""
                quantity = int(item_quantities[i]) if i < len(item_quantities) and item_quantities[i] else 0
                unit_price = Decimal(str(item_unit_prices[i] or 0)) if i < len(item_unit_prices) else Decimal("0")
                
                if name and quantity > 0 and unit_price >= 0:
                    line_total = unit_price * quantity
                    line_items.append({
                        "item_name": name,
                        "description": description,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": line_total,
                    })
            
            if not line_items:
                flash("Please add at least one valid line item.", "danger")
                return render_template(
                    "quotes/quotation_new.html",
                    clients=clients,
                    default_quote_date=default_quote_date.isoformat(),
                    default_expiry_date=default_expiry.isoformat(),
                )
            
            # Calculate totals - ensure no NULL arithmetic
            subtotal = sum(Decimal(str(item["line_total"])) for item in line_items)
            tax = subtotal * (Decimal(str(tax_rate)) / Decimal("100")) if tax_rate > 0 else Decimal("0.00")
            total = subtotal + tax
            
            # Create quotation
            quotation = Quotation(
                client_id=client_id,
                title=title or None,
                event_type=event_type or None,
                event_date=event_date,
                quote_date=quote_date,
                expiry_date=expiry_date,
                subtotal=subtotal,
                tax=tax,
                total=total,
            )
            db.session.add(quotation)
            db.session.flush()
            
            # Create line items
            for item_data in line_items:
                line = QuotationLine(
                    quotation_id=quotation.id,
                    item_name=item_data["item_name"],
                    description=item_data["description"] or None,
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"],
                    line_total=item_data["line_total"],
                )
                db.session.add(line)
            
            db.session.commit()
            flash(f"Quotation #{quotation.id} created successfully.", "success")
            return redirect(url_for("quotes.view_quote", quotation_id=quotation.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating quotation: {str(e)}", "danger")
            return render_template(
                "quotes/quotation_new.html",
                clients=clients,
                default_quote_date=default_quote_date.isoformat(),
                default_expiry_date=default_expiry.isoformat(),
            )
    
    # GET request - show form
    return render_template(
        "quotes/quotation_new.html",
        clients=clients,
        default_quote_date=default_quote_date.isoformat(),
        default_expiry_date=default_expiry.isoformat(),
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
            selected_event = db.session.get(Event, event_id)
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

        # Calculate totals properly
        quotation.subtotal = subtotal
        if not quotation.tax:
            quotation.tax = Decimal("0.00")
        if not quotation.total or quotation.total == 0:
            quotation.total = quotation.subtotal + quotation.tax
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
    from sas_management.utils.helpers import get_or_404
    quotation = (
        Quotation.query.options(joinedload(Quotation.lines), joinedload(Quotation.client), joinedload(Quotation.event))
        .filter(Quotation.id == quotation_id)
        .first()
    )
    if not quotation:
        from flask import abort
        abort(404)
    
    # Ensure totals are calculated correctly if missing
    if quotation.lines:
        calculated_subtotal = sum(Decimal(str(line.line_total or 0)) for line in quotation.lines)
        if quotation.subtotal != calculated_subtotal:
            quotation.subtotal = calculated_subtotal
        if not quotation.tax:
            quotation.tax = Decimal("0.00")
        if not quotation.total or quotation.total == 0:
            quotation.total = quotation.subtotal + quotation.tax
    
    # Check if invoice already exists for this event
    existing_invoice = None
    if quotation.event_id:
        existing_invoice = Invoice.query.filter_by(event_id=quotation.event_id).first()
    return render_template("quotes/view.html", quotation=quotation, existing_invoice=existing_invoice, date=date)

@quotes_bp.route("/convert/<int:quotation_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def convert_to_invoice(quotation_id):
    """Convert a quotation to an invoice."""
    from datetime import timedelta
    from sas_management.models import InvoiceStatus

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

@quotes_bp.route("/view/<int:quotation_id>/pdf")
@quotes_bp.route("/<int:quotation_id>/pdf")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def quotation_pdf(quotation_id):
    """Generate and download quotation PDF using HTML to PDF conversion."""
    quotation = (
        Quotation.query.options(joinedload(Quotation.lines), joinedload(Quotation.client), joinedload(Quotation.event))
        .filter(Quotation.id == quotation_id)
        .first()
    )
    if not quotation:
        from flask import abort
        abort(404)
    
    # Ensure totals are calculated correctly
    if quotation.lines:
        calculated_subtotal = sum(Decimal(str(line.line_total or 0)) for line in quotation.lines)
        if quotation.subtotal != calculated_subtotal:
            quotation.subtotal = calculated_subtotal
        if not quotation.tax:
            quotation.tax = Decimal("0.00")
        if not quotation.total or quotation.total == 0:
            quotation.total = quotation.subtotal + quotation.tax
    
    # Try ReportLab first (if available)
    try:
        from sas_management.services.quotation_service import generate_quotation_pdf
        pdf_path = generate_quotation_pdf(quotation_id)
        if os.path.exists(pdf_path):
            return send_file(
                pdf_path,
                download_name=f"quotation_{quotation.id}.pdf",
                mimetype='application/pdf'
            )
    except (ImportError, Exception) as e:
        # Fall back to HTML-based PDF generation
        current_app.logger.debug(f"ReportLab not available, using HTML fallback: {e}")
    
    # HTML-based PDF generation using weasyprint or pdfkit
    try:
        import weasyprint
        html_content = render_template("accounting/quotation_pdf.html", quotation=quotation)
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        from io import BytesIO
        pdf_buffer = BytesIO(pdf_bytes)
        return send_file(
            pdf_buffer,
            download_name=f"quotation_{quotation.id}.pdf",
            mimetype='application/pdf',
            as_attachment=True
        )
    except ImportError:
        try:
            import pdfkit
            html_content = render_template("accounting/quotation_pdf.html", quotation=quotation)
            pdf_bytes = pdfkit.from_string(html_content, False)
            from io import BytesIO
            pdf_buffer = BytesIO(pdf_bytes)
            return send_file(
                pdf_buffer,
                download_name=f"quotation_{quotation.id}.pdf",
                mimetype='application/pdf',
                as_attachment=True
            )
        except ImportError:
            # Last resort: return HTML view for printing
            flash("PDF generation libraries not available. Please use browser print function (Ctrl+P).", "info")
            return redirect(url_for("quotes.view_quote", quotation_id=quotation_id))
    except Exception as e:
        current_app.logger.exception(f"Error generating quotation PDF: {e}")
        flash(f"Error generating PDF: {str(e)}. Please use browser print function (Ctrl+P).", "warning")
        return redirect(url_for("quotes.view_quote", quotation_id=quotation_id))

@quotes_bp.route("/download-pdf/<int:quote_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def download_pdf(quote_id):
    """Alias for quotation_pdf for compatibility."""
    return quotation_pdf(quote_id)

@quotes_bp.route("/list")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def list_quotes():
    """List all quotations - alias for dashboard."""
    return redirect(url_for("quotes.dashboard"))

