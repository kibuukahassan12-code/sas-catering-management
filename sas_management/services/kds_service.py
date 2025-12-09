"""KDS service."""
from flask import current_app

def get_active_orders():
    """Get active orders for KDS display."""
    try:
        from models import POSOrder
        orders = POSOrder.query.filter(POSOrder.status.in_(['pending', 'preparing'])).order_by(POSOrder.created_at.desc()).limit(50).all()
        return {'success': True, 'orders': orders}
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error getting active orders: {e}")
        return {'success': False, 'error': str(e), 'orders': []}

