"""Vendor Management Service - Business logic for purchase orders and suppliers."""
import json
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError
import secrets

from models import PurchaseOrder, PurchaseOrderItem, Supplier, db


def generate_po_number() -> str:
    """Generate a unique purchase order number."""
    prefix = "PO"
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = secrets.token_hex(2)[:4].upper()
    return f"{prefix}-{timestamp}-{random_suffix}"


def create_purchase_order(
    supplier_id: int,
    user_id: int,
    po_date: str = None,
    expected_date: str = None,
    reference: str = None,
    items: List[Dict] = None,
    status: str = "open"
) -> PurchaseOrder:
    """Create a new purchase order with items."""
    try:
        # Validate supplier exists
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Parse dates
        if isinstance(po_date, str):
            po_date = datetime.fromisoformat(po_date).date() if po_date else date.today()
        elif po_date is None:
            po_date = date.today()
        
        if isinstance(expected_date, str) and expected_date:
            expected_date = datetime.fromisoformat(expected_date).date()
        else:
            expected_date = None
        
        # Generate PO number
        po_number = generate_po_number()
        
        # Calculate total from items
        total_amount = Decimal('0.00')
        if items:
            for item in items:
                qty = Decimal(str(item.get('qty', 0)))
                unit = Decimal(str(item.get('unit', 0)))
                tax = Decimal(str(item.get('tax', 0)))
                line_total = qty * unit * (1 + tax / 100)
                total_amount += line_total
        
        # Create purchase order
        po = PurchaseOrder(
            supplier_id=supplier_id,
            po_number=po_number,
            order_number=po_number,  # For compatibility
            po_date=po_date,
            order_date=po_date,  # For compatibility
            expected_date=expected_date,
            reference=reference,
            total_amount=total_amount,
            status=status,
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(po)
        db.session.flush()  # Get po.id
        
        # Create purchase order items
        if items:
            for item in items:
                desc = item.get('desc', '').strip()
                sku = item.get('sku', '').strip()
                qty = Decimal(str(item.get('qty', 0)))
                unit = Decimal(str(item.get('unit', 0)))
                tax = Decimal(str(item.get('tax', 0)))
                line_total = qty * unit * (1 + tax / 100)
                
                poi = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    description=desc,
                    sku=sku,
                    quantity=qty,
                    unit_cost=unit,
                    tax_percent=tax,
                    line_total=line_total
                )
                db.session.add(poi)
        
        db.session.commit()
        return po
        
    except SQLAlchemyError as e:
        db.session.rollback()
        raise Exception(f"Database error creating purchase order: {str(e)}")
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error creating purchase order: {str(e)}")


def get_purchase_order(po_id: int) -> Optional[PurchaseOrder]:
    """Get purchase order by ID."""
    try:
        return PurchaseOrder.query.get(po_id)
    except SQLAlchemyError as e:
        raise Exception(f"Database error getting purchase order: {str(e)}")


def list_purchase_orders(supplier_id: int = None, status: str = None) -> List[PurchaseOrder]:
    """List purchase orders with optional filters."""
    try:
        query = PurchaseOrder.query
        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(PurchaseOrder.created_at.desc()).all()
    except SQLAlchemyError as e:
        raise Exception(f"Database error listing purchase orders: {str(e)}")


def update_purchase_order_status(po_id: int, status: str) -> PurchaseOrder:
    """Update purchase order status."""
    try:
        po = PurchaseOrder.query.get_or_404(po_id)
        po.status = status
        po.updated_at = datetime.utcnow()
        db.session.commit()
        return po
    except SQLAlchemyError as e:
        db.session.rollback()
        raise Exception(f"Database error updating purchase order: {str(e)}")

