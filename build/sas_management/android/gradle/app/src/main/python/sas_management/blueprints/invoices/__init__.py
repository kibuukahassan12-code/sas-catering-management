from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from models import (
    Event,
    Invoice,
    InvoiceStatus,
    Receipt,
    Transaction,
    TransactionType,
    UserRole,
    db,
)
from utils import role_required, paginate_query

invoices_bp = Blueprint("invoices", __name__, url_prefix="/invoices")

def _generate_invoice_number():
    """Generate a unique invoice number."""
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

def _generate_receipt_number():
    """Generate a unique receipt number."""
    today = date.today()
    prefix = f"RCP-{today.strftime('%Y%m%d')}"
    last_receipt = (
        Receipt.query.filter(Receipt.receipt_number.like(f"{prefix}%"))
        .order_by(Receipt.receipt_number.desc())
        .first()
    )
    if last_receipt:
        try:
            last_num = int(last_receipt.receipt_number.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    return f"{prefix}-{new_num:04d}"

@invoices_bp.route("")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def invoice_list():
    pagination = paginate_query(
        Invoice.query.options(joinedload(Invoice.event))
        .order_by(Invoice.issue_date.desc())
    )
    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")
    return render_template("invoices/list.html", invoices=pagination.items, pagination=pagination, CURRENCY=CURRENCY)

@invoices_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def invoice_new():
    """Create a new invoice."""
    from models import Client
    
    if request.method == "POST":
        try:
            event_id = request.form.get("event_id", type=int) or None
            client_id = request.form.get("client_id", type=int)
            issue_date_str = request.form.get("issue_date")
            due_date_str = request.form.get("due_date")
            total_amount = Decimal(request.form.get("total_amount", "0") or "0")
            notes = request.form.get("notes", "").strip()
            
            if not client_id:
                flash("Please select a client.", "danger")
                return redirect(url_for("invoices.invoice_new"))
            
            if total_amount <= 0:
                flash("Invoice amount must be greater than 0.", "danger")
                return redirect(url_for("invoices.invoice_new"))
            
            # Parse dates
            try:
                issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d").date() if issue_date_str else date.today()
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else date.today() + timedelta(days=30)
            except ValueError:
                issue_date = date.today()
                due_date = date.today() + timedelta(days=30)
            
            # Generate invoice number
            invoice_number = _generate_invoice_number()
            
            # Create invoice
            invoice = Invoice(
                event_id=event_id,
                invoice_number=invoice_number,
                issue_date=issue_date,
                due_date=due_date,
                total_amount_ugx=total_amount,
                status=InvoiceStatus.Issued
            )
            db.session.add(invoice)
            db.session.flush()
            
            # Generate PDF
            try:
                from services.invoice_service import generate_invoice_pdf
                generate_invoice_pdf(invoice.id)
            except Exception as pdf_error:
                current_app.logger.warning(f"Could not generate PDF for invoice {invoice.id}: {pdf_error}")
            
            db.session.commit()
            flash(f"Invoice {invoice_number} created successfully!", "success")
            return redirect(url_for("invoices.invoice_view", invoice_id=invoice.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Error creating invoice: {e}")
            flash(f"Error creating invoice: {str(e)}", "danger")
            return redirect(url_for("invoices.invoice_new"))
    
    # GET request - show form
    events = Event.query.filter(Event.status.in_(["Confirmed", "In Progress"])).order_by(Event.event_date.desc()).limit(50).all()
    clients = Client.query.order_by(Client.name.asc()).all()
    default_issue_date = date.today().strftime('%Y-%m-%d')
    default_due_date = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")
    
    return render_template(
        "invoices/new.html",
        events=events,
        clients=clients,
        default_issue_date=default_issue_date,
        default_due_date=default_due_date,
        CURRENCY=CURRENCY
    )

@invoices_bp.route("/view/<int:invoice_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def invoice_view(invoice_id):
    invoice = (
        Invoice.query.options(joinedload(Invoice.event).joinedload(Event.client))
        .filter(Invoice.id == invoice_id)
        .first_or_404()
    )
    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")
    return render_template("invoices/view.html", invoice=invoice, CURRENCY=CURRENCY)

@invoices_bp.route("/<int:invoice_id>/pdf")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def invoice_pdf(invoice_id):
    """Generate and download invoice PDF."""
    from flask import send_file
    from services.invoice_service import generate_invoice_pdf
    
    invoice = Invoice.query.get_or_404(invoice_id)
    
    try:
        # Generate PDF if it doesn't exist
        pdf_path = generate_invoice_pdf(invoice_id)
        
        # Send file
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"invoice_{invoice.invoice_number}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        current_app.logger.exception(f"Error generating invoice PDF: {e}")
        flash(f"Error generating PDF: {str(e)}", "danger")
        return redirect(url_for("invoices.invoice_view", invoice_id=invoice_id))

@invoices_bp.route("/<int:invoice_id>/receipt/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def receipt_new(invoice_id):
    invoice = (
        Invoice.query.options(joinedload(Invoice.event))
        .filter(Invoice.id == invoice_id)
        .first_or_404()
    )

    if request.method == "POST":
        payment_date_str = request.form.get("payment_date", "")
        try:
            payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()
        except ValueError:
            payment_date = date.today()

        amount_received = Decimal(request.form.get("amount_received_ugx", "0") or "0")
        payment_method = request.form.get("payment_method", "Cash").strip()

        if amount_received <= 0:
            flash("Payment amount must be greater than zero.", "danger")
            return render_template("invoices/receipt_form.html", invoice=invoice)

        # Create receipt
        receipt = Receipt(
            invoice_id=invoice.id,
            receipt_number=_generate_receipt_number(),
            payment_date=payment_date,
            amount_received_ugx=amount_received,
            payment_method=payment_method,
        )
        db.session.add(receipt)

        # Update invoice status to Paid
        invoice.status = InvoiceStatus.Paid

        # Create cashbook income transaction
        income_transaction = Transaction(
            type=TransactionType.Income,
            category="Catering Sales",
            description=f"Payment received for Invoice {invoice.invoice_number}",
            amount=amount_received,
            date=payment_date,
            related_event_id=invoice.event_id,
        )
        db.session.add(income_transaction)

        db.session.commit()
        flash("Receipt generated and payment recorded successfully.", "success")
        return redirect(url_for("invoices.receipt_view", receipt_id=receipt.id))

    default_date = date.today().strftime('%Y-%m-%d')
    return render_template("invoices/receipt_form.html", invoice=invoice, default_date=default_date)

@invoices_bp.route("/receipt/<int:receipt_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def receipt_view(receipt_id):
    receipt = (
        Receipt.query.options(
            joinedload(Receipt.invoice).joinedload(Invoice.event).joinedload(Event.client)
        )
        .filter(Receipt.id == receipt_id)
        .first_or_404()
    )
    return render_template("invoices/receipt_view.html", receipt=receipt)

