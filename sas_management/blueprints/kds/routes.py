"""Kitchen Display System routes."""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import or_

from sas_management.models import db, POSOrder, POSOrderLine

kds_bp = Blueprint("kds", __name__, url_prefix="/kds")


@kds_bp.route("/screen")
@login_required
def screen():
    """KDS display screen with enhanced features."""
    # Get filter parameters
    status_filter = request.args.get("status", "active")  # active, pending, preparing, ready, all
    station_filter = request.args.get("station", "all")  # all, hot, cold, drinks, etc.
    
    # Build query
    try:
        query = POSOrder.query
        
        # Status filtering
        if status_filter == "active":
            query = query.filter(POSOrder.status.in_(['pending', 'preparing']))
        elif status_filter == "pending":
            query = query.filter(POSOrder.status == 'pending')
        elif status_filter == "preparing":
            query = query.filter(POSOrder.status == 'preparing')
        elif status_filter == "ready":
            query = query.filter(POSOrder.status == 'ready')
        # "all" shows everything
        
        # Order by creation time (oldest first for kitchen priority)
        query = query.order_by(POSOrder.created_at.asc())
        
        # Limit to last 50 orders
        orders = query.limit(50).all()
        
        # Get statistics
        stats = {
            'pending': POSOrder.query.filter(POSOrder.status == 'pending').count(),
            'preparing': POSOrder.query.filter(POSOrder.status == 'preparing').count(),
            'ready': POSOrder.query.filter(POSOrder.status == 'ready').count(),
            'total_active': POSOrder.query.filter(POSOrder.status.in_(['pending', 'preparing'])).count(),
        }
        
        return render_template(
            "kds/kds_screen.html",
            orders=orders,
            stats=stats,
            status_filter=status_filter,
            station_filter=station_filter,
            now=datetime.utcnow()
        )
    except Exception as e:
        return render_template(
            "kds/kds_screen.html",
            orders=[],
            stats={},
            status_filter="active",
            station_filter="all",
            now=datetime.utcnow()
        )


@kds_bp.route("/api/orders")
@login_required
def api_orders():
    """API endpoint for real-time order updates."""
    try:
        status_filter = request.args.get("status", "active")
        
        query = POSOrder.query
        if status_filter == "active":
            query = query.filter(POSOrder.status.in_(['pending', 'preparing']))
        elif status_filter != "all":
            query = query.filter(POSOrder.status == status_filter)
        
        orders = query.order_by(POSOrder.created_at.asc()).limit(50).all()
        
        orders_data = []
        for order in orders:
            # Get kitchen items only
            kitchen_items = [line for line in order.lines if line.is_kitchen_item]
            
            # Calculate elapsed time
            elapsed_seconds = (datetime.utcnow() - order.created_at).total_seconds()
            elapsed_minutes = int(elapsed_seconds // 60)
            
            orders_data.append({
                'id': order.id,
                'reference': order.reference,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'elapsed_minutes': elapsed_minutes,
                'is_delivery': order.is_delivery,
                'delivery_address': order.delivery_address,
                'client_name': order.client.name if order.client else None,
                'items': [{
                    'id': item.id,
                    'product_name': item.product_name,
                    'qty': int(item.qty),
                    'note': item.note,
                } for item in kitchen_items],
                'total_items': len(kitchen_items),
            })
        
        return jsonify({
            'success': True,
            'orders': orders_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@kds_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    """Update order status."""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'preparing', 'ready', 'completed']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        order = POSOrder.query.get_or_404(order_id)
        old_status = order.status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'old_status': old_status,
            'new_status': new_status
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@kds_bp.route("/orders/<int:order_id>/complete", methods=["POST"])
@login_required
def complete_order(order_id):
    """Mark order as ready (backward compatibility)."""
    try:
        order = POSOrder.query.get_or_404(order_id)
        order.status = 'ready'
        order.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@kds_bp.route("/orders/<int:order_id>/start", methods=["POST"])
@login_required
def start_order(order_id):
    """Start preparing an order."""
    try:
        order = POSOrder.query.get_or_404(order_id)
        if order.status == 'pending':
            order.status = 'preparing'
            order.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Order is not in pending status'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

