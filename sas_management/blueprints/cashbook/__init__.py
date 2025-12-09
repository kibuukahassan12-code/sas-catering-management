from datetime import date, datetime
from decimal import Decimal

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from models import Event, Transaction, TransactionType, UserRole, db
from utils import get_decimal, paginate_query, role_required
from utils.helpers import parse_date

cashbook_bp = Blueprint("cashbook", __name__, url_prefix="/cashbook")


def _coerce_transaction_type(value):
    if not value:
        return None
    for tx_type in TransactionType:
        if tx_type.value == value:
            return tx_type
    return None




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


def _sum_transactions_filtered(tx_type, start_date=None, end_date=None, category=None):
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


@cashbook_bp.route("/")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def index():
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
    income_total = _sum_transactions_filtered(TransactionType.Income, start_date, end_date, category)
    expense_total = _sum_transactions_filtered(TransactionType.Expense, start_date, end_date, category)
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
    }

    return render_template(
        "cashbook/index.html",
        transactions=pagination.items,
        pagination=pagination,
        summary=summary,
        transaction_types=TransactionType,
        categories=categories,
        start_date=start_date_str,
        end_date=end_date_str,
        selected_category=category,
        selected_type=tx_type_str,
    )


@cashbook_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def add_transaction():
    events = Event.query.order_by(Event.event_date.desc()).all()
    if request.method == "POST":
        tx_type = _coerce_transaction_type(request.form.get("type"))
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        amount = get_decimal(request.form.get("amount"))
        entry_date = parse_date(request.form.get("date"))
        related_event_id = request.form.get("related_event_id", type=int)

        if not tx_type:
            flash("Select whether this record is Income or Expense.", "danger")
            return render_template(
                "cashbook/transaction_form.html",
                action="Add",
                transaction=None,
                events=events,
                transaction_types=TransactionType,
                default_date=date.today().isoformat(),
            )
        if not category or not description:
            flash("Category and description are required.", "danger")
            return render_template(
                "cashbook/transaction_form.html",
                action="Add",
                transaction=None,
                events=events,
                transaction_types=TransactionType,
                default_date=date.today().isoformat(),
            )
        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return render_template(
                "cashbook/transaction_form.html",
                action="Add",
                transaction=None,
                events=events,
                transaction_types=TransactionType,
                default_date=date.today().isoformat(),
            )

        transaction = Transaction(
            type=tx_type,
            category=category,
            description=description,
            amount=amount,
            date=entry_date,
            related_event_id=related_event_id if related_event_id else None,
        )
        db.session.add(transaction)
        db.session.commit()
        flash("Transaction recorded successfully.", "success")
        return redirect(url_for("cashbook.index"))

    return render_template(
        "cashbook/transaction_form.html",
        action="Add",
        transaction=None,
        events=events,
        transaction_types=TransactionType,
        default_date=date.today().isoformat(),
    )


@cashbook_bp.route("/edit/<int:transaction_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    events = Event.query.order_by(Event.event_date.desc()).all()

    if request.method == "POST":
        tx_type = _coerce_transaction_type(request.form.get("type"))
        category = request.form.get("category", "").strip() or transaction.category
        description = request.form.get("description", "").strip() or transaction.description
        amount = get_decimal(request.form.get("amount"), fallback=str(transaction.amount))
        entry_date = parse_date(request.form.get("date"))
        related_event_id = request.form.get("related_event_id", type=int)

        if not tx_type:
            flash("Select whether this record is Income or Expense.", "danger")
            return render_template(
                "cashbook/transaction_form.html",
                action="Edit",
                transaction=transaction,
                events=events,
                transaction_types=TransactionType,
                default_date=date.today().isoformat(),
            )
        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return render_template(
                "cashbook/transaction_form.html",
                action="Edit",
                transaction=transaction,
                events=events,
                transaction_types=TransactionType,
                default_date=date.today().isoformat(),
            )

        transaction.type = tx_type
        transaction.category = category
        transaction.description = description
        transaction.amount = amount
        transaction.date = entry_date
        transaction.related_event_id = related_event_id if related_event_id else None

        db.session.commit()
        flash("Transaction updated.", "success")
        return redirect(url_for("cashbook.index"))

    return render_template(
        "cashbook/transaction_form.html",
        action="Edit",
        transaction=transaction,
        events=events,
        transaction_types=TransactionType,
        default_date=date.today().isoformat(),
    )


@cashbook_bp.route("/delete/<int:transaction_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted.", "info")
    return redirect(url_for("cashbook.index"))

