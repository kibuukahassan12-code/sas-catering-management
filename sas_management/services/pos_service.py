"""POS service layer for business logic."""
import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError

from sas_management.models import (
    CateringItem,
    BakeryItem,
    POSDevice,
    POSOrder,
    POSOrderLine,
    POSPayment,
    POSReceipt,
    POSShift,
    db,
)


def generate_pos_order_reference():
    """Generate a unique POS order reference."""
    prefix = "POS"
    timestamp = datetime.now().strftime("%Y%m%d")
    last_order = (
        POSOrder.query.filter(POSOrder.reference.like(f"{prefix}-{timestamp}-%"))
        .order_by(POSOrder.id.desc())
        .first()
    )
    if last_order and last_order.reference:
        try:
            last_num = int(last_order.reference.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    return f"{prefix}-{timestamp}-{new_num:04d}"


def generate_pos_receipt_ref():
    """Generate a unique receipt reference."""
    prefix = "RCPT"
    timestamp = datetime.now().strftime("%Y%m%d")
    last_receipt = (
        POSReceipt.query.filter(POSReceipt.receipt_ref.like(f"{prefix}-{timestamp}-%"))
        .order_by(POSReceipt.id.desc())
        .first()
    )
    if last_receipt and last_receipt.receipt_ref:
        try:
            last_num = int(last_receipt.receipt_ref.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    return f"{prefix}-{timestamp}-{new_num:04d}"


def create_order(payload, device_code=None, shift_id=None):
    """
    Create a POS order with line items.
    
    Args:
        payload: Dict with 'items', 'client_id', 'is_delivery', 'delivery_address', 'delivery_date', 'discount_amount', 'tax_rate'
        device_code: Optional device code
        shift_id: Optional shift ID
    
    Returns:
        POSOrder instance
    """
    try:
        # Validate required fields
        items = payload.get("items", [])
        if not items or len(items) == 0:
            raise ValueError("Order must contain at least one item")
        
        # Find device if provided
        device = None
        if device_code:
            device = POSDevice.query.filter_by(terminal_code=device_code, is_active=True).first()
            if not device:
                raise ValueError(f"Device '{device_code}' not found or inactive")
        
        # Validate shift if provided
        shift = None
        if shift_id:
            shift = db.session.get(POSShift, shift_id)
            if not shift:
                raise ValueError(f"Shift with ID {shift_id} not found")
            if shift.status != "open":
                raise ValueError(f"Cannot create order for closed shift (ID: {shift_id})")
        
        # Create order
        order = POSOrder(
            reference=generate_pos_order_reference(),
            shift_id=shift_id,
            device_id=device.id if device else None,
            client_id=payload.get("client_id"),
            is_delivery=payload.get("is_delivery", False),
            delivery_address=payload.get("delivery_address"),
            delivery_date=datetime.fromisoformat(payload["delivery_date"]) if payload.get("delivery_date") else None,
            discount_amount=Decimal(str(payload.get("discount_amount", 0))),
            status="draft",
        )
        db.session.add(order)
        db.session.flush()
        
        # Process line items
        subtotal = Decimal("0.00")
        tax_rate_percent = Decimal(str(payload.get("tax_rate", 0)))
        tax_rate = tax_rate_percent / 100  # Convert percentage to decimal (e.g., 18% -> 0.18)
        
        for idx, item in enumerate(items):
            try:
                product_id = item.get("product_id")
                product_name = item.get("product_name", "Unknown Product")
                qty = int(item.get("qty", 1))
                unit_price = Decimal(str(item.get("unit_price", 0)))
                
                # Validate item data
                if qty <= 0:
                    raise ValueError(f"Item {idx + 1}: Quantity must be greater than 0")
                if unit_price < 0:
                    raise ValueError(f"Item {idx + 1}: Unit price cannot be negative")
                
                line_total = unit_price * qty
                
                # Try to get product name from database if product_id provided
                if product_id:
                    catering_item = db.session.get(CateringItem, product_id)
                    bakery_item = db.session.get(BakeryItem, product_id)
                    if catering_item:
                        product_name = catering_item.name
                    elif bakery_item:
                        product_name = bakery_item.name
                
                line_item = POSOrderLine(
                    order_id=order.id,
                    product_id=product_id,
                    product_name=product_name,
                    qty=qty,
                    unit_price=unit_price,
                    line_total=line_total,
                    note=item.get("note"),
                    is_kitchen_item=item.get("is_kitchen_item", True),
                )
                db.session.add(line_item)
                subtotal += line_total
            except (ValueError, TypeError) as item_error:
                db.session.rollback()
                raise ValueError(f"Invalid item data at index {idx}: {str(item_error)}")
        
        # Calculate tax and total
        if subtotal < 0:
            db.session.rollback()
            raise ValueError("Order subtotal cannot be negative")
        
        order.tax_amount = subtotal * tax_rate
        order.total_amount = subtotal + order.tax_amount - order.discount_amount
        
        # Ensure total is not negative
        if order.total_amount < 0:
            order.total_amount = Decimal("0.00")
        
        db.session.commit()
        return order
        
    except ValueError as ve:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to create order: {str(e)}")


def add_payment(order_id, amount, method, ref=None, received_by=None):
    """
    Add payment to POS order and generate receipt.
    
    Args:
        order_id: POS order ID
        amount: Payment amount
        method: Payment method (cash, pos, mobile_money, etc.)
        ref: Optional payment reference
        received_by: Optional user ID who received payment
    
    Returns:
        Tuple of (POSPayment, POSReceipt)
    """
    try:
        # Validate and find order
        order = db.session.get(POSOrder, order_id)
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
        
        # Validate amount
        try:
            payment_amount = Decimal(str(amount))
            if payment_amount <= 0:
                raise ValueError("Payment amount must be greater than 0")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid payment amount: {str(e)}")
        
        # Validate method
        valid_methods = ["cash", "pos", "mobile_money", "bank_transfer", "credit_card"]
        if method and method not in valid_methods:
            raise ValueError(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
        
        # Create payment record - this happens FIRST to track payment immediately
        payment = POSPayment(
            order_id=order.id,
            amount=payment_amount,
            method=method or "cash",
            reference=ref,  # Use 'reference' field name from model
        )
        db.session.add(payment)
        db.session.flush()  # Flush to get payment.id for receipt
        
        # Generate receipt IMMEDIATELY after payment is created (before finalizing)
        # This ensures receipt is available before payment is fully processed
        receipt_ref = generate_pos_receipt_ref()
        receipt_number = receipt_ref  # auto-fill because DB requires NOT NULL
        receipt = POSReceipt(receipt_number=receipt_number, 
            order_id=order.id,
            payment_id=payment.id,
            receipt_ref=receipt_ref,
            issued_at=datetime.utcnow(),
        )
        db.session.add(receipt)
        db.session.flush()  # Flush to ensure receipt is saved
        
        # Update order status based on total payments
        # Recalculate total paid including this payment
        total_paid = sum(Decimal(str(p.amount)) for p in order.payments) + payment_amount
        if total_paid >= order.total_amount:
            order.status = "paid"
        elif total_paid > 0:
            order.status = "partially_paid"
        
        # Refresh to ensure all relationships are loaded
        db.session.refresh(payment)
        db.session.refresh(receipt)
        db.session.refresh(order)
        
        # Commit all changes: payment, receipt, and order status update
        db.session.commit()
        
        # Return payment and receipt - receipt is now generated before final processing
        return payment, receipt
        
    except ValueError as ve:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to add payment: {str(e)}")


def close_shift(shift_id, ending_cash, cash_count=None):
    """
    Close a POS shift and generate Z-report.
    
    Args:
        shift_id: Shift ID
        ending_cash: Ending cash amount
        cash_count: Optional physical cash count
    
    Returns:
        Dict with shift summary and Z-report data
    """
    try:
        db.session.begin()
        
        shift = POSShift.query.get_or_404(shift_id)
        if shift.status == "closed":
            raise ValueError("Shift is already closed")
        
        shift.ending_cash = Decimal(str(ending_cash))
        shift.ended_at = datetime.utcnow()
        shift.status = "closed"
        
        # Get all orders for this shift
        orders = POSOrder.query.filter_by(shift_id=shift_id).all()
        
        # Calculate totals
        total_sales = sum(Decimal(str(o.total_amount)) for o in orders if o.status == "paid")
        total_tax = sum(Decimal(str(o.tax_amount)) for o in orders if o.status == "paid")
        total_discount = sum(Decimal(str(o.discount_amount)) for o in orders if o.status == "paid")
        
        # Group payments by method
        payments_by_method = {}
        for order in orders:
            for payment in order.payments:
                method = payment.method
                if method not in payments_by_method:
                    payments_by_method[method] = Decimal("0.00")
                payments_by_method[method] += Decimal(str(payment.amount))
        
        # Calculate variance
        expected_cash = Decimal(str(shift.starting_cash)) + payments_by_method.get("cash", Decimal("0.00"))
        variance = Decimal(str(ending_cash)) - expected_cash
        
        z_report = {
            "shift_id": shift.id,
            "cashier_id": shift.user_id,
            "started_at": shift.started_at.isoformat(),
            "ended_at": shift.ended_at.isoformat(),
            "starting_cash": float(shift.starting_cash),
            "ending_cash": float(shift.ending_cash),
            "expected_cash": float(expected_cash),
            "variance": float(variance),
            "total_sales": float(total_sales),
            "total_tax": float(total_tax),
            "total_discount": float(total_discount),
            "orders_count": len(orders),
            "payments_by_method": {k: float(v) for k, v in payments_by_method.items()},
        }
        
        db.session.commit()
        return z_report
        
    except Exception as e:
        db.session.rollback()
        raise


def reserve_inventory_for_order(order_id):
    """
    Reserve inventory for POS order (if items require inventory).
    This is a placeholder - integrate with inventory service as needed.
    """
    # TODO: Integrate with inventory service
    # For now, just return success
    return True


def release_inventory(order_id):
    """
    Release reserved inventory (on cancellation or refund).
    """
    # TODO: Integrate with inventory service
    return True


def generate_kitchen_tickets(order_id):
    """
    Generate kitchen tickets for order items marked as kitchen items.
    
    Returns:
        List of kitchen ticket data
    """
    order = POSOrder.query.get_or_404(order_id)
    kitchen_items = [line for line in order.lines if line.is_kitchen_item]
    
    tickets = []
    for item in kitchen_items:
        tickets.append({
            "product_name": item.product_name,
            "qty": item.qty,
            "note": item.note,
            "order_ref": order.reference,
            "order_time": order.order_time.isoformat(),
        })
    
    return tickets


def sync_orders_for_offline(device_code, orders_list):
    """
    Sync batched orders from offline terminal.
    
    Args:
        device_code: Device terminal code
        orders_list: List of order dicts with temporary refs
    
    Returns:
        Dict mapping temp_refs to final_refs
    """
    try:
        device = POSDevice.query.filter_by(terminal_code=device_code, is_active=True).first()
        if not device:
            raise ValueError(f"Device {device_code} not found")
        
        device.last_seen = datetime.utcnow()
        
        ref_mapping = {}
        for order_data in orders_list:
            temp_ref = order_data.get("temp_ref")
            # Create order with final reference
            order = create_order(order_data, device_code=device_code)
            ref_mapping[temp_ref] = order.reference
        
        db.session.commit()
        return ref_mapping
        
    except Exception as e:
        db.session.rollback()
        raise


def generate_z_report(shift_id):
    """Generate Z-report for shift (same as close_shift but without closing)."""
    shift = POSShift.query.get_or_404(shift_id)
    orders = POSOrder.query.filter_by(shift_id=shift_id).all()
    
    total_sales = sum(Decimal(str(o.total_amount)) for o in orders if o.status == "paid")
    total_tax = sum(Decimal(str(o.tax_amount)) for o in orders if o.status == "paid")
    total_discount = sum(Decimal(str(o.discount_amount)) for o in orders if o.status == "paid")
    
    payments_by_method = {}
    for order in orders:
        for payment in order.payments:
            method = payment.method
            if method not in payments_by_method:
                payments_by_method[method] = Decimal("0.00")
            payments_by_method[method] += Decimal(str(payment.amount))
    
    return {
        "shift_id": shift.id,
        "started_at": shift.started_at.isoformat(),
        "total_sales": float(total_sales),
        "total_tax": float(total_tax),
        "total_discount": float(total_discount),
        "orders_count": len(orders),
        "payments_by_method": {k: float(v) for k, v in payments_by_method.items()},
    }

