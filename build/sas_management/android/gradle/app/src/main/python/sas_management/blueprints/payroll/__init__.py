from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.orm import joinedload

from models import PayrollRecord, Transaction, TransactionType, User, UserRole, db
from utils import get_decimal, paginate_query, role_required
from utils.helpers import parse_date

payroll_bp = Blueprint("payroll", __name__, url_prefix="/admin/payroll")


@payroll_bp.route("")
@login_required
@role_required(UserRole.Admin)
def payroll_list():
    pagination = paginate_query(
        PayrollRecord.query.options(joinedload(PayrollRecord.user))
        .order_by(PayrollRecord.pay_date.desc())
    )
    return render_template(
        "payroll/list.html", payroll_records=pagination.items, pagination=pagination
    )


@payroll_bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin)
def payroll_add():
    users = User.query.order_by(User.email.asc()).all()

    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        pay_date_str = request.form.get("pay_date", "")
        amount_str = request.form.get("amount_ugx", "0")
        description = request.form.get("description", "").strip() or "Monthly Salary"

        if not user_id:
            flash("Select a staff member.", "danger")
            return render_template(
                "payroll/form.html",
                action="Add",
                payroll_record=None,
                users=users,
                default_date=date.today().isoformat(),
            )

        pay_date = parse_date(pay_date_str)
        amount = get_decimal(amount_str)

        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return render_template(
                "payroll/form.html",
                action="Add",
                payroll_record=None,
                users=users,
                default_date=date.today().isoformat(),
            )

        # Create payroll record
        payroll_record = PayrollRecord(
            user_id=user_id,
            pay_date=pay_date,
            amount_ugx=amount,
            description=description,
        )
        db.session.add(payroll_record)
        db.session.flush()

        # Automatically create cashbook expense transaction
        expense_transaction = Transaction(
            type=TransactionType.Expense,
            category="Salaries/Wages",
            description=f"Payroll: {description}",
            amount=amount,
            date=pay_date,
            related_event_id=None,
        )
        db.session.add(expense_transaction)

        db.session.commit()
        flash("Payroll record created and cashbook expense recorded successfully.", "success")
        return redirect(url_for("payroll.payroll_list"))

    return render_template(
        "payroll/form.html",
        action="Add",
        payroll_record=None,
        users=users,
        default_date=date.today().isoformat(),
    )


@payroll_bp.route("/edit/<int:payroll_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin)
def payroll_edit(payroll_id):
    payroll_record = PayrollRecord.query.get_or_404(payroll_id)
    users = User.query.order_by(User.email.asc()).all()

    if request.method == "POST":
        user_id = request.form.get("user_id", type=int) or payroll_record.user_id
        pay_date_str = request.form.get("pay_date", "")
        amount_str = request.form.get("amount_ugx", str(payroll_record.amount_ugx))
        description = request.form.get("description", "").strip() or payroll_record.description

        pay_date = parse_date(pay_date_str) if pay_date_str else payroll_record.pay_date
        amount = get_decimal(amount_str)

        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return render_template(
                "payroll/form.html",
                action="Edit",
                payroll_record=payroll_record,
                users=users,
                default_date=payroll_record.pay_date.isoformat(),
            )

        payroll_record.user_id = user_id
        payroll_record.pay_date = pay_date
        payroll_record.amount_ugx = amount
        payroll_record.description = description

        db.session.commit()
        flash("Payroll record updated successfully.", "success")
        return redirect(url_for("payroll.payroll_list"))

    return render_template(
        "payroll/form.html",
        action="Edit",
        payroll_record=payroll_record,
        users=users,
        default_date=payroll_record.pay_date.isoformat(),
    )


@payroll_bp.route("/delete/<int:payroll_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def payroll_delete(payroll_id):
    payroll_record = PayrollRecord.query.get_or_404(payroll_id)
    db.session.delete(payroll_record)
    db.session.commit()
    flash("Payroll record deleted.", "info")
    return redirect(url_for("payroll.payroll_list"))

