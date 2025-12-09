"""Additional routes for accounting module."""
from datetime import date
from flask import send_file, abort, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import os

from models import AccountingReceipt, UserRole, db
from sqlalchemy.orm import joinedload
from utils import role_required

# Import the existing blueprint
from blueprints.accounting import accounting_bp


@accounting_bp.route("/receipts")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def receipts_list():
    """List all receipts."""
    from models import AccountingPayment, Invoice, Client, Event
    
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 20)
    
    query = (
        AccountingReceipt.query
        .options(
            joinedload(AccountingReceipt.payment).joinedload(AccountingPayment.invoice).joinedload(Invoice.event).joinedload(Event.client)
        )
        .order_by(AccountingReceipt.date.desc())
    )
    
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    
    return render_template(
        "accounting/receipts_list.html",
        receipts=pagination.items,
        pagination=pagination,
        CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX ")
    )


@accounting_bp.route("/receipts/<int:receipt_id>/view")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def view_receipt(receipt_id):
    """
    View receipt PDF file.
    Receipts are stored with relative path: receipts/receipt_{receipt.reference}.pdf
    Opens PDF ready for download.
    If PDF doesn't exist, generates it on-the-fly.
    """
    from models import AccountingPayment, Invoice, Client, User, Event, db
    
    # Import PDF generation function - handle gracefully if ReportLab not available
    try:
        from services.accounting_service import _generate_pdf_receipt, REPORTLAB_AVAILABLE
        _generate_pdf_fn = _generate_pdf_receipt
        reportlab_available = REPORTLAB_AVAILABLE
    except (ImportError, AttributeError) as e:
        reportlab_available = False
        _generate_pdf_fn = None
        try:
            current_app.logger.warning(f"ReportLab not available: {e}")
        except:
            pass
    
    receipt = AccountingReceipt.query.get(receipt_id)
    
    if not receipt:
        abort(404, description="Receipt not found")
    
    # Construct expected relative path
    pdf_relative_path = f"receipts/receipt_{receipt.reference}.pdf"
    full_path = os.path.join(current_app.instance_path, pdf_relative_path)
    full_path = os.path.abspath(full_path)
    
    # If PDF path is missing or file doesn't exist, generate it
    if not receipt.pdf_path or not os.path.exists(full_path):
        if not reportlab_available or not _generate_pdf_fn:
            abort(500, description="PDF generation not available. ReportLab is not installed. Please install it using: pip install reportlab")
        
        try:
            # Get related data for PDF generation
            payment = None
            if hasattr(receipt, 'payment') and receipt.payment:
                payment = receipt.payment
            elif receipt.payment_id:
                payment = AccountingPayment.query.get(receipt.payment_id)
            
            if not payment:
                abort(404, description="Payment not found for this receipt")
            
            invoice = None
            if payment.invoice_id:
                invoice = Invoice.query.get(payment.invoice_id)
            
            client = None
            if receipt.issued_to:
                client = Client.query.get(receipt.issued_to)
            elif invoice and invoice.event_id:
                event = Event.query.get(invoice.event_id)
                if event and event.client_id:
                    client = Client.query.get(event.client_id)
            
            issuer = None
            if receipt.issued_by:
                issuer = User.query.get(receipt.issued_by)
            
            # Ensure receipts folder exists
            receipts_folder = os.path.join(current_app.instance_path, "receipts")
            os.makedirs(receipts_folder, exist_ok=True)
            
            # Generate PDF
            _generate_pdf_fn(
                pdf_path=full_path,
                receipt=receipt,
                payment=payment,
                invoice=invoice,
                client=client,
                issuer=issuer
            )
            
            # Update receipt with PDF path
            receipt.pdf_path = pdf_relative_path
            db.session.commit()
            
            current_app.logger.info(f"Generated PDF for receipt {receipt_id} at {full_path}")
        
        except Exception as e:
            current_app.logger.exception(f"Error generating PDF for receipt {receipt_id}: {e}")
            abort(500, description=f"Failed to generate receipt PDF: {str(e)}. Please ensure ReportLab is installed: pip install reportlab")
    
    # Verify file exists before serving
    if not os.path.exists(full_path):
        abort(404, description=f"Receipt PDF file not found at: {full_path}")
    
    return send_file(
        full_path,
        mimetype="application/pdf",
        as_attachment=False,  # Display in browser (set True to force download)
        download_name=f"receipt_{receipt.reference}.pdf"
    )


@accounting_bp.route("/receipts/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def receipt_new():
    """Create a new receipt manually."""
    from models import AccountingPayment, Invoice, Client, User, Event
    from services.accounting_service import generate_receipt, record_payment
    
    if request.method == "POST":
        try:
            client_id = request.form.get("client_id", type=int)
            invoice_id = request.form.get("invoice_id", type=int) or None
            amount = request.form.get("amount", type=float)
            method = request.form.get("method", "cash")
            payment_date = request.form.get("payment_date")
            notes = request.form.get("notes", "").strip()
            
            if not amount or amount <= 0:
                flash("Amount must be greater than 0.", "danger")
                return redirect(url_for("accounting.receipt_new"))
            
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
                    return redirect(url_for("accounting.receipt_new"))
            
            client = Client.query.get_or_404(client_id)
            
            # Parse payment date
            if payment_date:
                from datetime import datetime
                payment_date = datetime.strptime(payment_date, "%Y-%m-%d").date()
            else:
                payment_date = date.today()
            
            payment = None
            
            # If invoice is provided, record payment for that invoice
            if invoice_id:
                try:
                    payment, receipt = record_payment(
                        invoice_id=invoice_id,
                        amount=amount,
                        method=method,
                        received_by=current_user.id,
                        payment_date=payment_date
                    )
                    if notes:
                        receipt.notes = notes
                        db.session.commit()
                    flash(f"Payment recorded and receipt {receipt.reference} created successfully!", "success")
                    return redirect(url_for("accounting.view_receipt", receipt_id=receipt.id))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error recording payment: {str(e)}", "danger")
                    return redirect(url_for("accounting.receipt_new"))
            
            # Create standalone receipt (will create payment automatically)
            receipt = generate_receipt(
                payment_id=None,
                issued_by=current_user.id,
                amount=amount,
                client_id=client_id,
                method=method,
                receipt_date=payment_date,
                notes=notes
            )
            
            flash(f"Receipt {receipt.reference} created successfully!", "success")
            return redirect(url_for("accounting.view_receipt", receipt_id=receipt.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Error creating receipt: {e}")
            flash(f"Error creating receipt: {str(e)}", "danger")
            return redirect(url_for("accounting.receipt_new"))
    
    # GET request - show form
    from models import InvoiceStatus
    clients = Client.query.order_by(Client.name.asc()).all()
    invoices = Invoice.query.filter(Invoice.status != InvoiceStatus.Paid).order_by(Invoice.issue_date.desc()).limit(50).all()
    
    return render_template(
        "accounting/receipt_new.html",
        clients=clients,
        invoices=invoices,
        default_date=date.today().strftime('%Y-%m-%d'),
        CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX ")
    )


@accounting_bp.route("/receipts/<int:receipt_id>/print")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def print_receipt(receipt_id):
    """Print-friendly receipt view."""
    from models import AccountingPayment, Invoice, Client, User, Event
    
    receipt = AccountingReceipt.query.get_or_404(receipt_id)
    
    # Get related data
    payment = None
    if hasattr(receipt, 'payment') and receipt.payment:
        payment = receipt.payment
    elif receipt.payment_id:
        payment = AccountingPayment.query.get(receipt.payment_id)
    
    invoice = None
    if payment and payment.invoice_id:
        invoice = Invoice.query.get(payment.invoice_id)
    
    client = None
    if receipt.issued_to:
        client = Client.query.get(receipt.issued_to)
    elif invoice and invoice.event_id:
        event = Event.query.get(invoice.event_id)
        if event and event.client_id:
            client = Client.query.get(event.client_id)
    
    issuer = None
    if receipt.issued_by:
        issuer = User.query.get(receipt.issued_by)
    
    return render_template(
        "accounting/receipt_print.html",
        receipt=receipt,
        payment=payment,
        invoice=invoice,
        client=client,
        issuer=issuer,
        CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX ")
    )
