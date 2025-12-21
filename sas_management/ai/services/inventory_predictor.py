"""
Inventory Predictor AI Service

Predicts inventory shortages and provides quantity projections.
"""
from flask import current_app
from datetime import date, timedelta


def run(payload, user):
    """
    Run Inventory Predictor AI service.
    
    Args:
        payload: dict with 'date_range' (days) or 'start_date' and 'end_date'
        user: Current user object
    
    Returns:
        dict: {
            'success': bool,
            'items_likely_to_run_out': list,
            'quantity_projections': list,
            'error': str (if failed)
        }
    """
    try:
        from sas_management.models import InventoryItem, Event
        
        # Determine date range
        if 'date_range' in payload:
            days = int(payload.get('date_range', 30))
            start_date = date.today()
            end_date = start_date + timedelta(days=days)
        else:
            start_date = payload.get('start_date')
            end_date = payload.get('end_date')
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)
            if not start_date:
                start_date = date.today()
            if not end_date:
                end_date = start_date + timedelta(days=30)
        
        # Get upcoming events in range
        upcoming_events = Event.query.filter(
            Event.date >= start_date,
            Event.date <= end_date
        ).all()
        
        # Get all inventory items
        all_items = InventoryItem.query.filter_by(status='Available').all()
        
        items_likely_to_run_out = []
        quantity_projections = []
        
        for item in all_items:
            current_stock = item.stock_count or 0
            
            # Simple prediction: if stock is low, flag it
            reorder_level = getattr(item, 'reorder_level', 10)
            if not hasattr(item, 'reorder_level'):
                # Estimate reorder level as 20% of typical usage
                reorder_level = max(10, int(current_stock * 0.2))
            
            # Project usage based on upcoming events
            projected_usage = len(upcoming_events) * 2  # Simple heuristic
            
            projected_quantity = current_stock - projected_usage
            
            if current_stock <= reorder_level or projected_quantity < 0:
                items_likely_to_run_out.append({
                    'item_id': item.id,
                    'item_name': item.name,
                    'current_quantity': current_stock,
                    'reorder_level': reorder_level,
                    'risk_level': 'critical' if current_stock <= reorder_level * 0.5 else 'high',
                    'days_until_shortage': max(1, int(projected_quantity / (projected_usage / 30))) if projected_usage > 0 else 999
                })
            
            quantity_projections.append({
                'item_id': item.id,
                'item_name': item.name,
                'current_quantity': current_stock,
                'projected_quantity': max(0, projected_quantity),
                'projected_usage': projected_usage,
                'recommended_order': max(0, reorder_level * 2 - projected_quantity) if projected_quantity < reorder_level else 0
            })
        
        # Sort by risk
        items_likely_to_run_out.sort(key=lambda x: 0 if x['risk_level'] == 'critical' else 1)
        
        return {
            'success': True,
            'items_likely_to_run_out': items_likely_to_run_out[:20],  # Top 20
            'quantity_projections': quantity_projections,
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'upcoming_events': len(upcoming_events)
            }
        }
        
    except Exception as e:
        current_app.logger.exception(f"Inventory Predictor AI error: {e}")
        return {
            'success': False,
            'error': str(e),
            'items_likely_to_run_out': [],
            'quantity_projections': []
        }
