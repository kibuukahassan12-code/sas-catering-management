"""
Bakery Department Service Layer
Handles business logic for bakery orders, production, and inventory integration.
"""

from datetime import datetime, date
from decimal import Decimal
import os
from flask import current_app
from sqlalchemy import func

from sas_management.models import (
    db, BakeryOrder, BakeryOrderItem, BakeryItem, BakeryProductionTask,
    Ingredient, InventoryItem, User, Client
)


def generate_order_reference():
    """Generate unique bakery order reference."""
    today = date.today().strftime("%Y%m%d")
    last_order = BakeryOrder.query.order_by(BakeryOrder.id.desc()).first()
    if last_order:
        last_num = int(last_order.id)
    else:
        last_num = 0
    new_num = last_num + 1
    return f"BAK-{today}-{new_num:04d}"


def create_bakery_order(customer_id=None, customer_name=None, customer_phone=None,
                        customer_email=None, pickup_date=None, delivery_address=None,
                        bakery_notes=None, created_by=None):
    """
    Create a new bakery order.
    
    Returns:
        BakeryOrder instance
    """
    try:
        order = BakeryOrder(
            customer_id=customer_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            order_status="Draft",
            pickup_date=pickup_date,
            delivery_address=delivery_address,
            bakery_notes=bakery_notes,
            created_by=created_by,
            total_amount=Decimal("0.00")
        )
        db.session.add(order)
        db.session.flush()  # Get the ID
        db.session.commit()
        return order
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating bakery order: {e}")
        raise


def add_item_to_order(order_id, item_id=None, item_name=None, qty=1, 
                     custom_price=None, custom_notes=None):
    """
    Add an item to a bakery order.
    
    Returns:
        BakeryOrderItem instance
    """
    try:
        order = BakeryOrder.query.get_or_404(order_id)
        
        # Get item details if item_id provided
        if item_id:
            item = db.session.get(BakeryItem, item_id)
            if not item:
                raise ValueError(f"Bakery item {item_id} not found")
            item_name = item.name
            if not custom_price:
                custom_price = item.get_current_price()
        else:
            if not item_name:
                raise ValueError("Either item_id or item_name must be provided")
            if not custom_price:
                raise ValueError("custom_price required for custom items")
        
        order_item = BakeryOrderItem(
            order_id=order_id,
            item_id=item_id,
            item_name=item_name,
            qty=qty,
            custom_price=Decimal(str(custom_price)),
            custom_notes=custom_notes
        )
        db.session.add(order_item)
        
        # Recalculate order total
        _recalculate_order_total(order_id)
        db.session.commit()
        return order_item
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error adding item to order: {e}")
        raise


def _recalculate_order_total(order_id):
    """Recalculate total amount for a bakery order."""
    order = db.session.get(BakeryOrder, order_id)
    if not order:
        return
    
    total = Decimal("0.00")
    for item in order.items:
        item_total = (item.custom_price or Decimal("0.00")) * item.qty
        total += item_total
    
    order.total_amount = total
    db.session.flush()


def update_order_status(order_id, new_status):
    """
    Update bakery order status.
    If status changes to "In Production", deduct ingredients from inventory.
    
    Returns:
        Updated BakeryOrder instance
    """
    try:
        order = BakeryOrder.query.get_or_404(order_id)
        old_status = order.order_status
        order.order_status = new_status
        order.updated_at = datetime.utcnow()
        
        # If moving to "In Production", consume ingredients
        if old_status != "In Production" and new_status == "In Production":
            consume_ingredients_for_order(order_id)
        
        db.session.commit()
        return order
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating order status: {e}")
        raise


def consume_ingredients_for_order(order_id):
    """
    Consume ingredients from inventory when order enters production.
    This is a simplified version - in a full implementation, you'd have
    a recipe system mapping bakery items to ingredients.
    
    For now, this is a placeholder that can be extended.
    """
    try:
        order = BakeryOrder.query.get_or_404(order_id)
        
        # TODO: Implement ingredient consumption based on recipes
        # For now, this is a placeholder
        # Example logic:
        # for order_item in order.items:
        #     if order_item.item_id:
        #         # Get recipe for this bakery item
        #         # Deduct ingredients from inventory
        #         pass
        
        current_app.logger.info(f"Ingredient consumption for order {order_id} - placeholder")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error consuming ingredients: {e}")
        raise


def assign_production_task(order_id, staff_id, task_type, notes=None):
    """
    Assign a production task to staff.
    
    Returns:
        BakeryProductionTask instance
    """
    try:
        task = BakeryProductionTask(
            order_id=order_id,
            staff_id=staff_id,
            task_type=task_type,
            status="Pending",
            notes=notes
        )
        db.session.add(task)
        db.session.commit()
        return task
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error assigning production task: {e}")
        raise


def start_production_task(task_id):
    """Mark a production task as started."""
    try:
        task = BakeryProductionTask.query.get_or_404(task_id)
        task.status = "In Progress"
        task.start_time = datetime.utcnow()
        db.session.commit()
        return task
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error starting task: {e}")
        raise


def complete_production_task(task_id, notes=None):
    """Mark a production task as completed."""
    try:
        task = BakeryProductionTask.query.get_or_404(task_id)
        task.status = "Completed"
        task.end_time = datetime.utcnow()
        if notes:
            task.notes = notes
        db.session.commit()
        return task
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error completing task: {e}")
        raise


def get_daily_sales(start_date=None, end_date=None):
    """Get daily sales report for bakery."""
    try:
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = date.today()
        
        orders = BakeryOrder.query.filter(
            BakeryOrder.order_status.in_(["Ready", "Completed"]),
            BakeryOrder.created_at >= datetime.combine(start_date, datetime.min.time()),
            BakeryOrder.created_at <= datetime.combine(end_date, datetime.max.time())
        ).all()
        
        total_sales = sum(float(order.total_amount) for order in orders)
        order_count = len(orders)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_sales": total_sales,
            "order_count": order_count,
            "orders": orders
        }
    except Exception as e:
        current_app.logger.exception(f"Error getting daily sales: {e}")
        return {"total_sales": 0, "order_count": 0, "orders": []}


def get_top_items(limit=10, start_date=None, end_date=None):
    """Get top selling bakery items."""
    try:
        query = db.session.query(
            BakeryOrderItem.item_name,
            func.sum(BakeryOrderItem.qty).label('total_qty'),
            func.sum(BakeryOrderItem.qty * BakeryOrderItem.custom_price).label('total_revenue')
        ).join(BakeryOrder).filter(
            BakeryOrder.order_status.in_(["Ready", "Completed"])
        )
        
        if start_date:
            query = query.filter(BakeryOrder.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(BakeryOrder.created_at <= datetime.combine(end_date, datetime.max.time()))
        
        results = query.group_by(BakeryOrderItem.item_name).order_by(
            func.sum(BakeryOrderItem.qty).desc()
        ).limit(limit).all()
        
        return [
            {
                "item_name": row.item_name,
                "total_qty": int(row.total_qty),
                "total_revenue": float(row.total_revenue or 0)
            }
            for row in results
        ]
    except Exception as e:
        current_app.logger.exception(f"Error getting top items: {e}")
        return []


def get_staff_productivity(staff_id=None, start_date=None, end_date=None):
    """Get staff productivity report."""
    try:
        query = db.session.query(
            BakeryProductionTask.staff_id,
            User.email,
            func.count(BakeryProductionTask.id).label('task_count'),
            func.sum(
                func.extract('epoch', BakeryProductionTask.end_time - BakeryProductionTask.start_time) / 3600
            ).label('total_hours')
        ).join(User).filter(
            BakeryProductionTask.status == "Completed"
        )
        
        if staff_id:
            query = query.filter(BakeryProductionTask.staff_id == staff_id)
        if start_date:
            query = query.filter(BakeryProductionTask.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            query = query.filter(BakeryProductionTask.created_at <= datetime.combine(end_date, datetime.max.time()))
        
        results = query.group_by(BakeryProductionTask.staff_id, User.email).all()
        
        return [
            {
                "staff_id": row.staff_id,
                "staff_email": row.email,
                "task_count": int(row.task_count),
                "total_hours": float(row.total_hours or 0)
            }
            for row in results
        ]
    except Exception as e:
        current_app.logger.exception(f"Error getting staff productivity: {e}")
        return []

