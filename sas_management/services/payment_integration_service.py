"""
Payment Integration Service

This service ensures all payments from Hire, Bakery, and Events departments
are automatically recorded in the Cashbook and reflected in Revenue charts.

Features:
- Auto-record payments to Cashbook transactions
- Track pending invoice amounts from all departments
- Provide unified revenue data for charts
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from flask import current_app
from calendar import month_abbr

from sas_management.models import (
    db,
    Transaction,
    TransactionType,
    Order,  # Hire Order
    BakeryOrder,
    Event,
    Invoice,
    InvoiceStatus,
    Receipt,
    AccountingPayment,
)


def record_payment_to_cashbook(
    amount,
    category,
    description,
    department,
    related_event_id=None,
    payment_date=None,
    reference_id=None,
    reference_type=None
):
    """
    Record a payment as an Income transaction in the Cashbook.
    
    Args:
        amount: Payment amount (Decimal or float)
        category: Category for the transaction (e.g., "Hire Payment", "Bakery Sales")
        description: Description of the payment
        department: Source department (hire, bakery, events)
        related_event_id: Optional event ID to link the transaction
        payment_date: Date of payment (defaults to today)
        reference_id: ID of the source record (e.g., order_id, invoice_id)
        reference_type: Type of source record (e.g., "hire_order", "bakery_order")
    
    Returns:
        Transaction object if successful, None if failed
    """
    try:
        if not amount or Decimal(str(amount)) <= 0:
            current_app.logger.warning(f"Invalid payment amount: {amount}")
            return None
        
        amount_decimal = Decimal(str(amount))
        tx_date = payment_date or date.today()
        
        # Build comprehensive description
        full_description = f"[{department.upper()}] {description}"
        if reference_id and reference_type:
            full_description += f" (Ref: {reference_type}#{reference_id})"
        
        # Check for duplicate transaction to avoid double-recording
        existing = Transaction.query.filter(
            Transaction.type == TransactionType.Income,
            Transaction.category == category,
            Transaction.description == full_description,
            Transaction.amount == amount_decimal,
            Transaction.date == tx_date
        ).first()
        
        if existing:
            current_app.logger.info(f"Transaction already exists: {existing.id}")
            return existing
        
        # Create new transaction
        transaction = Transaction(
            type=TransactionType.Income,
            category=category,
            description=full_description,
            amount=amount_decimal,
            date=tx_date,
            related_event_id=related_event_id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        current_app.logger.info(
            f"Recorded {department} payment to cashbook: {amount_decimal} - {description}"
        )
        
        return transaction
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error recording payment to cashbook: {e}")
        return None


def record_hire_payment(order, payment_amount, payment_date=None):
    """
    Record a Hire department payment to Cashbook.
    
    Args:
        order: Order (Hire Order) object
        payment_amount: Amount being paid
        payment_date: Date of payment
    
    Returns:
        Transaction object if successful
    """
    description = f"Hire Order #{order.id}"
    if order.client_name:
        description += f" - {order.client_name}"
    if order.reference:
        description += f" ({order.reference})"
    
    return record_payment_to_cashbook(
        amount=payment_amount,
        category="Hire Payment",
        description=description,
        department="hire",
        related_event_id=order.event_id if hasattr(order, 'event_id') else None,
        payment_date=payment_date,
        reference_id=order.id,
        reference_type="hire_order"
    )


def record_bakery_payment(order, payment_amount, payment_date=None):
    """
    Record a Bakery department payment to Cashbook.
    
    Args:
        order: BakeryOrder object
        payment_amount: Amount being paid
        payment_date: Date of payment
    
    Returns:
        Transaction object if successful
    """
    description = f"Bakery Order #{order.id}"
    if hasattr(order, 'client') and order.client:
        description += f" - {order.client.name}"
    elif hasattr(order, 'customer_name') and order.customer_name:
        description += f" - {order.customer_name}"
    
    return record_payment_to_cashbook(
        amount=payment_amount,
        category="Bakery Sales",
        description=description,
        department="bakery",
        related_event_id=order.event_id if hasattr(order, 'event_id') else None,
        payment_date=payment_date,
        reference_id=order.id,
        reference_type="bakery_order"
    )


def record_event_payment(event, payment_amount, payment_date=None, invoice=None):
    """
    Record an Event department payment to Cashbook.
    
    Args:
        event: Event object
        payment_amount: Amount being paid
        payment_date: Date of payment
        invoice: Optional Invoice object
    
    Returns:
        Transaction object if successful
    """
    description = f"Event: {event.title or event.event_name or 'Untitled'}"
    if event.client_name:
        description += f" - {event.client_name}"
    if invoice:
        description += f" (Invoice #{invoice.invoice_number})"
    
    return record_payment_to_cashbook(
        amount=payment_amount,
        category="Event Payment",
        description=description,
        department="events",
        related_event_id=event.id,
        payment_date=payment_date,
        reference_id=event.id,
        reference_type="event"
    )


def get_pending_invoice_amount():
    """
    Calculate total pending invoice amount from all departments.
    
    Returns:
        Decimal: Total pending amount
    """
    total_pending = Decimal('0.00')
    
    try:
        # 1. Pending Invoices (Events)
        pending_invoices = (
            db.session.query(db.func.coalesce(db.func.sum(Invoice.total_amount_ugx), 0))
            .filter(Invoice.status.in_([InvoiceStatus.Issued, InvoiceStatus.Draft]))
            .scalar()
        )
        total_pending += Decimal(str(pending_invoices or 0))
        
        # 2. Pending Hire Orders (balance_due > 0)
        try:
            pending_hire = (
                db.session.query(db.func.coalesce(db.func.sum(Order.balance_due), 0))
                .filter(Order.balance_due > 0)
                .filter(Order.status != 'Cancelled')
                .scalar()
            )
            total_pending += Decimal(str(pending_hire or 0))
        except Exception as e:
            current_app.logger.warning(f"Error getting pending hire amounts: {e}")
        
        # 3. Pending Bakery Orders (unpaid orders)
        try:
            # Bakery orders that are not completed and have total_amount
            pending_bakery = (
                db.session.query(db.func.coalesce(db.func.sum(BakeryOrder.total_amount), 0))
                .filter(BakeryOrder.status.notin_(['Completed', 'Delivered', 'Cancelled', 'Paid']))
                .scalar()
            )
            total_pending += Decimal(str(pending_bakery or 0))
        except Exception as e:
            current_app.logger.warning(f"Error getting pending bakery amounts: {e}")
        
    except Exception as e:
        current_app.logger.exception(f"Error calculating pending invoice amount: {e}")
    
    return total_pending


def get_department_revenue_breakdown(start_date=None, end_date=None):
    """
    Get revenue breakdown by department for a date range.
    
    Args:
        start_date: Start date (defaults to 30 days ago)
        end_date: End date (defaults to today)
    
    Returns:
        dict: Revenue breakdown by department
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    breakdown = {
        "events": Decimal('0.00'),
        "hire": Decimal('0.00'),
        "bakery": Decimal('0.00'),
        "other": Decimal('0.00'),
        "total": Decimal('0.00')
    }
    
    try:
        # Get income transactions grouped by category
        transactions = Transaction.query.filter(
            Transaction.type == TransactionType.Income,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        for tx in transactions:
            category_lower = (tx.category or '').lower()
            if 'event' in category_lower or 'catering' in category_lower:
                breakdown["events"] += tx.amount
            elif 'hire' in category_lower:
                breakdown["hire"] += tx.amount
            elif 'bakery' in category_lower:
                breakdown["bakery"] += tx.amount
            else:
                breakdown["other"] += tx.amount
        
        breakdown["total"] = sum([
            breakdown["events"],
            breakdown["hire"],
            breakdown["bakery"],
            breakdown["other"]
        ])
        
    except Exception as e:
        current_app.logger.exception(f"Error getting revenue breakdown: {e}")
    
    return breakdown


def get_monthly_revenue_data(months=6):
    """
    Get monthly revenue and expense data for charts.
    Includes all departments: Events, Hire, and Bakery.
    
    Args:
        months: Number of months to include (default 6)
    
    Returns:
        dict: Monthly revenue data with labels, revenue, expenses, and bookings
    """
    today = date.today()
    
    labels = []
    revenue = []
    expenses = []
    bookings = []
    
    for i in range(months - 1, -1, -1):
        # Calculate month boundaries
        month_start = (today - timedelta(days=i * 30)).replace(day=1)
        # Get last day of month
        if month_start.month == 12:
            month_end = month_start.replace(day=31)
        else:
            month_end = (month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1))
        
        month_label = f"{month_abbr[month_start.month]} {month_start.year}"
        labels.append(month_label)
        
        # Calculate income for this month
        try:
            income = (
                db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0))
                .filter(Transaction.type == TransactionType.Income)
                .filter(Transaction.date >= month_start)
                .filter(Transaction.date <= month_end)
                .scalar()
            )
            revenue.append(float(income or 0))
        except Exception as e:
            current_app.logger.warning(f"Error getting monthly income: {e}")
            revenue.append(0)
        
        # Calculate expenses for this month
        try:
            expense = (
                db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0))
                .filter(Transaction.type == TransactionType.Expense)
                .filter(Transaction.date >= month_start)
                .filter(Transaction.date <= month_end)
                .scalar()
            )
            expenses.append(float(expense or 0))
        except Exception as e:
            current_app.logger.warning(f"Error getting monthly expenses: {e}")
            expenses.append(0)
        
        # Calculate bookings (events) for this month
        try:
            booking_count = Event.query.filter(
                Event.event_date >= month_start,
                Event.event_date <= month_end
            ).count()
            bookings.append(booking_count)
        except Exception as e:
            current_app.logger.warning(f"Error getting monthly bookings: {e}")
            bookings.append(0)
    
    return {
        "labels": labels,
        "revenue": revenue,
        "expenses": expenses,
        "bookings": bookings
    }


def sync_existing_payments_to_cashbook():
    """
    Sync existing payments from all departments to Cashbook.
    This is a one-time operation to backfill historical payments.
    
    Returns:
        dict: Summary of synced payments
    """
    summary = {
        "hire_payments": 0,
        "bakery_payments": 0,
        "event_payments": 0,
        "errors": []
    }
    
    try:
        # 1. Sync Hire Order payments
        hire_orders = Order.query.filter(Order.amount_paid > 0).all()
        for order in hire_orders:
            try:
                tx = record_hire_payment(
                    order=order,
                    payment_amount=order.amount_paid,
                    payment_date=order.created_at.date() if order.created_at else date.today()
                )
                if tx:
                    summary["hire_payments"] += 1
            except Exception as e:
                summary["errors"].append(f"Hire Order {order.id}: {str(e)}")
        
        # 2. Sync Bakery Order payments (completed orders)
        bakery_orders = BakeryOrder.query.filter(
            BakeryOrder.status.in_(['Completed', 'Delivered', 'Paid'])
        ).all()
        for order in bakery_orders:
            try:
                if order.total_amount and order.total_amount > 0:
                    tx = record_bakery_payment(
                        order=order,
                        payment_amount=order.total_amount,
                        payment_date=order.created_at.date() if order.created_at else date.today()
                    )
                    if tx:
                        summary["bakery_payments"] += 1
            except Exception as e:
                summary["errors"].append(f"Bakery Order {order.id}: {str(e)}")
        
        # 3. Sync Event Invoice payments (paid invoices via Receipt)
        receipts = Receipt.query.all()
        for receipt in receipts:
            try:
                if receipt.amount_received_ugx and receipt.amount_received_ugx > 0:
                    # Get associated invoice and event
                    invoice = receipt.invoice
                    if invoice and invoice.event:
                        tx = record_event_payment(
                            event=invoice.event,
                            payment_amount=receipt.amount_received_ugx,
                            payment_date=receipt.payment_date,
                            invoice=invoice
                        )
                        if tx:
                            summary["event_payments"] += 1
            except Exception as e:
                summary["errors"].append(f"Receipt {receipt.id}: {str(e)}")
        
        current_app.logger.info(
            f"Synced payments to cashbook: Hire={summary['hire_payments']}, "
            f"Bakery={summary['bakery_payments']}, Events={summary['event_payments']}"
        )
        
    except Exception as e:
        current_app.logger.exception(f"Error syncing payments to cashbook: {e}")
        summary["errors"].append(str(e))
    
    return summary


def get_all_pending_amounts():
    """
    Get breakdown of all pending amounts by department.
    
    Returns:
        dict: Pending amounts breakdown
    """
    result = {
        "events": {
            "count": 0,
            "amount": Decimal('0.00'),
            "label": "Events / Catering"
        },
        "hire": {
            "count": 0,
            "amount": Decimal('0.00'),
            "label": "Hire Department"
        },
        "bakery": {
            "count": 0,
            "amount": Decimal('0.00'),
            "label": "Bakery"
        },
        "total_pending": Decimal('0.00')
    }
    
    try:
        # Pending Invoices (Events)
        pending_invoices = Invoice.query.filter(
            Invoice.status.in_([InvoiceStatus.Issued, InvoiceStatus.Draft])
        ).all()
        result["events"]["count"] = len(pending_invoices)
        result["events"]["amount"] = sum(
            Decimal(str(i.total_amount_ugx or 0)) for i in pending_invoices
        )
        
        # Pending Hire Orders
        pending_hire = Order.query.filter(
            Order.balance_due > 0,
            Order.status != 'Cancelled'
        ).all()
        result["hire"]["count"] = len(pending_hire)
        result["hire"]["amount"] = sum(
            Decimal(str(o.balance_due or 0)) for o in pending_hire
        )
        
        # Pending Bakery Orders
        pending_bakery = BakeryOrder.query.filter(
            BakeryOrder.status.notin_(['Completed', 'Delivered', 'Cancelled', 'Paid'])
        ).all()
        result["bakery"]["count"] = len(pending_bakery)
        result["bakery"]["amount"] = sum(
            Decimal(str(o.total_amount or 0)) for o in pending_bakery
        )
        
        # Total
        result["total_pending"] = (
            result["events"]["amount"] +
            result["hire"]["amount"] +
            result["bakery"]["amount"]
        )
        
    except Exception as e:
        current_app.logger.exception(f"Error getting pending amounts: {e}")
    
    return result


def get_department_revenue_summary(start_date=None, end_date=None):
    """
    Get comprehensive revenue summary by department.
    
    Args:
        start_date: Start date for filtering (defaults to all time)
        end_date: End date for filtering (defaults to today)
    
    Returns:
        dict: Revenue breakdown by department with totals
    """
    if not end_date:
        end_date = date.today()
    
    result = {
        "events": {
            "revenue": Decimal('0.00'),
            "paid_count": 0,
            "label": "Events / Catering"
        },
        "hire": {
            "revenue": Decimal('0.00'),
            "paid_count": 0,
            "label": "Hire Department"
        },
        "bakery": {
            "revenue": Decimal('0.00'),
            "paid_count": 0,
            "label": "Bakery"
        },
        "other": {
            "revenue": Decimal('0.00'),
            "paid_count": 0,
            "label": "Other Income"
        },
        "total_revenue": Decimal('0.00'),
        "total_transactions": 0
    }
    
    try:
        # Build query for income transactions
        query = Transaction.query.filter(Transaction.type == TransactionType.Income)
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        transactions = query.all()
        
        for tx in transactions:
            category_lower = (tx.category or '').lower()
            description_lower = (tx.description or '').lower()
            
            # Categorize by department
            if 'event' in category_lower or 'catering' in category_lower or '[events]' in description_lower:
                result["events"]["revenue"] += tx.amount
                result["events"]["paid_count"] += 1
            elif 'hire' in category_lower or '[hire]' in description_lower:
                result["hire"]["revenue"] += tx.amount
                result["hire"]["paid_count"] += 1
            elif 'bakery' in category_lower or '[bakery]' in description_lower:
                result["bakery"]["revenue"] += tx.amount
                result["bakery"]["paid_count"] += 1
            else:
                result["other"]["revenue"] += tx.amount
                result["other"]["paid_count"] += 1
        
        result["total_revenue"] = (
            result["events"]["revenue"] +
            result["hire"]["revenue"] +
            result["bakery"]["revenue"] +
            result["other"]["revenue"]
        )
        result["total_transactions"] = (
            result["events"]["paid_count"] +
            result["hire"]["paid_count"] +
            result["bakery"]["paid_count"] +
            result["other"]["paid_count"]
        )
        
    except Exception as e:
        current_app.logger.exception(f"Error getting department revenue summary: {e}")
    
    return result


def get_complete_financial_summary():
    """
    Get complete financial summary for all departments.
    Includes both revenue (paid) and pending amounts.
    
    Returns:
        dict: Complete financial summary with departments breakdown
    """
    # Get revenue by department
    revenue = get_department_revenue_summary()
    
    # Get pending by department
    pending = get_all_pending_amounts()
    
    # Combine into comprehensive summary
    summary = {
        "departments": {
            "events": {
                "label": "Events / Catering",
                "revenue": float(revenue["events"]["revenue"]),
                "paid_count": revenue["events"]["paid_count"],
                "pending_amount": float(pending["events"]["amount"]),
                "pending_count": pending["events"]["count"],
            },
            "hire": {
                "label": "Hire Department",
                "revenue": float(revenue["hire"]["revenue"]),
                "paid_count": revenue["hire"]["paid_count"],
                "pending_amount": float(pending["hire"]["amount"]),
                "pending_count": pending["hire"]["count"],
            },
            "bakery": {
                "label": "Bakery",
                "revenue": float(revenue["bakery"]["revenue"]),
                "paid_count": revenue["bakery"]["paid_count"],
                "pending_amount": float(pending["bakery"]["amount"]),
                "pending_count": pending["bakery"]["count"],
            },
            "other": {
                "label": "Other Income",
                "revenue": float(revenue["other"]["revenue"]),
                "paid_count": revenue["other"]["paid_count"],
                "pending_amount": 0.0,
                "pending_count": 0,
            },
        },
        "totals": {
            "total_revenue": float(revenue["total_revenue"]),
            "total_pending": float(pending["total_pending"]),
            "total_paid_transactions": revenue["total_transactions"],
            "total_pending_count": (
                pending["events"]["count"] +
                pending["hire"]["count"] +
                pending["bakery"]["count"]
            ),
        }
    }
    
    return summary
