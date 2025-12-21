"""Accounting Department Blueprint."""
import os
from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from sas_management.models import (
    Account,
    AccountingPayment,
    AccountingReceipt,
    BankStatement,
    Client,
    Invoice,
    InvoiceStatus,
    Journal,
    JournalEntry,
    JournalEntryLine,
    UserRole,
    db,
)
from sas_management.utils import paginate_query, role_required, permission_required
# Import all functions from accounting_service to avoid ImportError
# This ensures no import errors even if some functions are temporarily missing
from sas_management.services.accounting_service import *

accounting_bp = Blueprint("accounting", __name__, url_prefix="/accounting")

# Import routes from routes.py to register additional routes
try:
    from blueprints.accounting import routes  # This will register the PDF route
except ImportError:
    pass  # routes.py is optional


# HTML Views

@accounting_bp.route("/dashboard")
@login_required
# @permission_required("accounting")
def dashboard():
    """Accounting dashboard."""
    try:
        # Initialize defaults
        total_invoices = paid_invoices = pending_invoices = 0
        total_receipts = total_payments = 0
        total_revenue = pending_amount = 0.0
        recent_payments = []
        account_balances = None
        
        # Get summary statistics with error handling
        try:
            total_invoices = Invoice.query.count()
            paid_invoices = Invoice.query.filter_by(status=InvoiceStatus.Paid).count()
            pending_invoices = Invoice.query.filter(Invoice.status.in_([InvoiceStatus.Issued, InvoiceStatus.Draft])).count()
        except Exception as e:
            current_app.logger.warning(f"Error querying invoices: {e}")
        
        try:
            total_receipts = AccountingReceipt.query.count()
            total_payments = AccountingPayment.query.count()
        except Exception as e:
            current_app.logger.warning(f"Error querying receipts/payments: {e}")
        
        # Calculate total revenue (sum of all paid invoice amounts)
        try:
            from sqlalchemy import func
            total_revenue = db.session.query(func.sum(Invoice.total_amount_ugx)).filter_by(status=InvoiceStatus.Paid).scalar() or 0
            pending_amount = db.session.query(func.sum(Invoice.total_amount_ugx)).filter(
                Invoice.status.in_([InvoiceStatus.Issued, InvoiceStatus.Draft])
            ).scalar() or 0
        except Exception as e:
            current_app.logger.warning(f"Error calculating revenue: {e}")
        
        # Get recent payments
        try:
            recent_payments = AccountingPayment.query.order_by(AccountingPayment.date.desc(), AccountingPayment.id.desc()).limit(10).all()
        except Exception as e:
            current_app.logger.warning(f"Error querying recent payments: {e}")
        
        summary = {
            "total_invoices": total_invoices,
            "paid_invoices": paid_invoices,
            "pending_invoices": pending_invoices,
            "total_receipts": total_receipts,
            "total_payments": total_payments,
            "total_revenue": float(total_revenue) if total_revenue else 0.0,
            "pending_amount": float(pending_amount) if pending_amount else 0.0,
        }
        
        # Get account balances for key accounts (Admin only) - Admin bypass
        if (hasattr(current_user, 'is_admin') and current_user.is_admin) or current_user.is_super_admin() or current_user.role == UserRole.Admin:
            try:
                trial_balance = compute_trial_balance()
                # Filter to key accounts (Cash, Bank, AR, Revenue, etc.)
                key_account_codes = ["1000", "1100", "1200", "4000", "2000"]
                account_balances = [acc for acc in trial_balance if acc.get("code") in key_account_codes][:10]
            except Exception as e:
                current_app.logger.exception(f"Error computing trial balance: {e}")
                account_balances = []
        
        return render_template(
            "accounting/accounting_dashboard.html",
            summary=summary,
            recent_payments=recent_payments or [],
            account_balances=account_balances,
            CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX ")
        )
    except Exception as e:
        current_app.logger.exception(f"Error in accounting dashboard: {e}")
        flash(f"Error loading dashboard: {str(e)}", "error")
        # Return a minimal dashboard with error message
        return render_template(
            "accounting/accounting_dashboard.html",
            summary={
                "total_invoices": 0,
                "paid_invoices": 0,
                "pending_invoices": 0,
                "total_receipts": 0,
                "total_payments": 0,
                "total_revenue": 0.0,
                "pending_amount": 0.0,
            },
            recent_payments=[],
            account_balances=None,
            CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX ")
        )


# Receipt PDF view route is now in routes.py


@accounting_bp.route("/journal")
@login_required
@role_required(UserRole.Admin)
def journal_view():
    """View journal entries."""
    entries = JournalEntry.query.order_by(JournalEntry.date.desc()).limit(50).all()
    return render_template("accounting/journal_view.html", entries=entries)


# REST API Endpoints

@accounting_bp.route("/api/accounts")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_accounts_list():
    """API: List chart of accounts."""
    accounts = Account.query.order_by(Account.code.asc()).all()
    return jsonify({
        "status": "success",
        "accounts": [
            {
                "id": acc.id,
                "code": acc.code,
                "name": acc.name,
                "type": acc.type,
                "parent_id": acc.parent_id,
                "currency": acc.currency,
            }
            for acc in accounts
        ],
    })


@accounting_bp.route("/api/accounts", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def api_account_create():
    """API: Create account."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    try:
        account = Account(
            code=data.get("code"),
            name=data.get("name"),
            parent_id=data.get("parent_id"),
            type=data.get("type"),
            currency=data.get("currency", "UGX"),
        )
        db.session.add(account)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Account created",
            "account_id": account.id,
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400


@accounting_bp.route("/api/invoices")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_invoices_list():
    """API: List invoices."""
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 10)
    
    query = Invoice.query.order_by(Invoice.issue_date.desc())
    pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "status": "success",
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "issue_date": inv.issue_date.isoformat(),
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "total_amount_ugx": float(inv.total_amount_ugx or 0),
                "status": inv.status.value,
            }
            for inv in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "pages": pagination.pages,
            "per_page": pagination.per_page,
            "total": pagination.total,
        },
    })


@accounting_bp.route("/api/invoices", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_invoice_create():
    """API: Create invoice."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    try:
        invoice = create_invoice(data)
        return jsonify({
            "status": "success",
            "message": "Invoice created",
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@accounting_bp.route("/api/invoices/<int:invoice_id>/send", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_invoice_send(invoice_id):
    """API: Send invoice (change status from Draft to Issued)."""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.status == InvoiceStatus.Draft:
        invoice.status = InvoiceStatus.Issued
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Invoice sent",
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": f"Invoice is already {invoice.status.value}. Only Draft invoices can be sent.",
        }), 400


@accounting_bp.route("/api/invoices/<int:invoice_id>/payments", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_invoice_payment(invoice_id):
    """API: Record payment for invoice."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    try:
        payment, receipt = record_payment(
            invoice_id=invoice_id,
            amount=data.get("amount"),
            method=data.get("method", "cash"),
            account_id=data.get("account_id"),
            received_by=current_user.id,
        )
        
        return jsonify({
            "status": "success",
            "message": "Payment recorded and receipt generated",
            "payment_id": payment.id,
            "receipt_id": receipt.id,
            "receipt_reference": receipt.reference,
            "pdf_path": receipt.pdf_path,
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@accounting_bp.route("/api/payments/<int:payment_id>/receipt", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_generate_receipt(payment_id):
    """API: Generate receipt for payment."""
    try:
        receipt = generate_receipt(payment_id)
        return jsonify({
            "status": "success",
            "message": "Receipt generated",
            "receipt_id": receipt.id,
            "receipt_reference": receipt.reference,
            "pdf_path": receipt.pdf_path,
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@accounting_bp.route("/api/receipts/<int:receipt_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_receipt_detail(receipt_id):
    """API: Get receipt details."""
    receipt = AccountingReceipt.query.get_or_404(receipt_id)
    payment = receipt.payment
    invoice = payment.invoice if payment.invoice_id else None
    
    return jsonify({
        "status": "success",
        "receipt": {
            "id": receipt.id,
            "reference": receipt.reference,
            "date": receipt.date.isoformat(),
            "amount": float(receipt.amount),
            "currency": receipt.currency,
            "method": receipt.method,
            "notes": receipt.notes,
            "pdf_path": receipt.pdf_path,
            "payment": {
                "id": payment.id,
                "reference": payment.reference,
                "amount": float(payment.amount),
            },
            "invoice": {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
            } if invoice else None,
        },
    })


@accounting_bp.route("/api/journal-entries")
@login_required
@role_required(UserRole.Admin)
def api_journal_entries_list():
    """API: List journal entries."""
    entries = JournalEntry.query.order_by(JournalEntry.date.desc()).limit(100).all()
    
    return jsonify({
        "status": "success",
        "entries": [
            {
                "id": entry.id,
                "reference": entry.reference,
                "date": entry.date.isoformat(),
                "narration": entry.narration,
                "journal_name": entry.journal.name if entry.journal else None,
                "lines_count": len(entry.lines),
            }
            for entry in entries
        ],
    })


@accounting_bp.route("/api/journal-entries", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def api_journal_entry_create():
    """API: Create manual journal entry."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    try:
        entry = create_journal_entry(
            lines=data.get("lines", []),
            journal_name=data.get("journal_name", "General Journal"),
            entry_date=data.get("date", date.today().isoformat()),
            reference=data.get("reference", ""),
            narration=data.get("narration", ""),
            created_by=current_user.id,
        )
        
        return jsonify({
            "status": "success",
            "message": "Journal entry created",
            "entry_id": entry.id,
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@accounting_bp.route("/api/trial-balance")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_trial_balance():
    """API: Get trial balance."""
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    
    date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
    date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None
    
    trial_balance = compute_trial_balance(date_from_obj, date_to_obj)
    
    return jsonify({
        "status": "success",
        "trial_balance": trial_balance,
    })


# PDF receipt route is now defined in routes.py
# The route will be automatically registered when routes.py is imported

