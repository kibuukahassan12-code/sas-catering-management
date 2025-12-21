import csv
from datetime import date, datetime
from decimal import Decimal
from io import StringIO

from flask import Blueprint, flash, make_response, redirect, render_template, request, url_for
from flask_login import login_required

from sas_management.models import Transaction, TransactionType, UserRole, db
from sas_management.utils import paginate_query, role_required
from sas_management.utils.helpers import parse_date

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _get_filtered_query(start_date=None, end_date=None, category=None, tx_type=None):
    """Build a filtered query for transactions."""
    query = Transaction.query

    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if category:
        query = query.filter(Transaction.category == category)
    if tx_type:
        query = query.filter(Transaction.type == tx_type)

    return query.order_by(Transaction.date.desc(), Transaction.id.desc())


def _sum_transactions(tx_type, start_date=None, end_date=None, category=None):
    """Calculate sum of transactions with filters."""
    query = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(
        Transaction.type == tx_type
    )

    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if category:
        query = query.filter(Transaction.category == category)

    value = query.scalar()
    return Decimal(value or 0)


@reports_bp.route("")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def reports_index():
    # Get filter parameters
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")
    category = request.args.get("category", "")
    tx_type_str = request.args.get("type", "")

    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None
    tx_type = None
    if tx_type_str:
        try:
            tx_type = TransactionType(tx_type_str)
        except ValueError:
            pass

    # Get filtered transactions
    filtered_query = _get_filtered_query(start_date, end_date, category, tx_type)
    pagination = paginate_query(filtered_query)

    # Calculate summary with filters
    income_total = _sum_transactions(TransactionType.Income, start_date, end_date, category)
    expense_total = _sum_transactions(TransactionType.Expense, start_date, end_date, category)
    net_profit = income_total - expense_total

    # Get unique categories for filter dropdown
    categories = (
        db.session.query(Transaction.category)
        .distinct()
        .order_by(Transaction.category.asc())
        .all()
    )
    categories = [cat[0] for cat in categories]

    summary = {
        "income": income_total,
        "expense": expense_total,
        "net": net_profit,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "category": category,
        "type": tx_type_str,
    }

    return render_template(
        "reports/index.html",
        transactions=pagination.items,
        pagination=pagination,
        summary=summary,
        categories=categories,
        transaction_types=TransactionType,
        start_date=start_date_str,
        end_date=end_date_str,
        selected_category=category,
        selected_type=tx_type_str,
    )


@reports_bp.route("/export")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def export_csv():
    """Export transactions to CSV with current filters."""
    start_date_str = request.args.get("start_date", "")
    end_date_str = request.args.get("end_date", "")
    category = request.args.get("category", "")
    tx_type_str = request.args.get("type", "")

    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None
    tx_type = None
    if tx_type_str:
        try:
            tx_type = TransactionType(tx_type_str)
        except ValueError:
            pass

    # Get filtered transactions (no pagination for export)
    filtered_query = _get_filtered_query(start_date, end_date, category, tx_type)
    transactions = filtered_query.all()

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category", "Description", "Amount (UGX)", "Event ID"])

    for tx in transactions:
        writer.writerow(
            [
                tx.date.isoformat(),
                tx.type.value,
                tx.category,
                tx.description,
                str(tx.amount),
                tx.related_event_id or "",
            ]
        )

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = 'attachment; filename="transactions_export.csv"'

    return response

