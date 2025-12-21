"""
Pricing Recommendation AI Service

Provides intelligent pricing recommendations based on costs and sales history.
"""
from flask import current_app
from statistics import mean


def run(payload, user):
    """
    Run Pricing Recommendation AI service.
    
    Args:
        payload: dict with 'item_id' or 'event_id' or 'item_name'
        user: Current user object
    
    Returns:
        dict: {
            'success': bool,
            'suggested_price': float,
            'margin_impact': dict,
            'pricing_analysis': dict,
            'error': str (if failed)
        }
    """
    try:
        from sas_management.models import InventoryItem, Event, MenuPackage
        
        item_id = payload.get('item_id')
        event_id = payload.get('event_id')
        item_name = payload.get('item_name')
        
        if item_id:
            # Inventory item pricing
            item = InventoryItem.query.get(item_id)
            if not item:
                return {
                    'success': False,
                    'error': f'Item with ID {item_id} not found',
                    'suggested_price': 0.0,
                    'margin_impact': {},
                    'pricing_analysis': {}
                }
            
            return _analyze_item_pricing(item)
        
        elif event_id:
            # Event pricing
            event = Event.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': f'Event with ID {event_id} not found',
                    'suggested_price': 0.0,
                    'margin_impact': {},
                    'pricing_analysis': {}
                }
            
            return _analyze_event_pricing(event)
        
        elif item_name:
            # Find item by name
            item = InventoryItem.query.filter_by(name=item_name).first()
            if item:
                return _analyze_item_pricing(item)
            else:
                return {
                    'success': False,
                    'error': f'Item "{item_name}" not found',
                    'suggested_price': 0.0,
                    'margin_impact': {},
                    'pricing_analysis': {}
                }
        
        else:
            return {
                'success': False,
                'error': 'item_id, event_id, or item_name is required',
                'suggested_price': 0.0,
                'margin_impact': {},
                'pricing_analysis': {}
            }
        
    except Exception as e:
        current_app.logger.exception(f"Pricing AI error: {e}")
        return {
            'success': False,
            'error': str(e),
            'suggested_price': 0.0,
            'margin_impact': {},
            'pricing_analysis': {}
        }


def _analyze_item_pricing(item):
    """Analyze and suggest pricing for inventory item."""
    current_price = float(item.unit_price_ugx or 0)
    cost = float(item.replacement_cost or item.unit_price_ugx or 0)
    
    # Standard margin: 30-50% for inventory items
    if cost > 0:
        suggested_price = cost * 1.4  # 40% margin
    else:
        suggested_price = current_price * 1.1 if current_price > 0 else 10000  # 10% increase or default
    
    margin_percentage = ((suggested_price - cost) / cost * 100) if cost > 0 else 0
    
    # Compare with current price
    price_change = suggested_price - current_price
    price_change_percent = (price_change / current_price * 100) if current_price > 0 else 0
    
    return {
        'success': True,
        'suggested_price': round(suggested_price, 2),
        'current_price': round(current_price, 2),
        'cost': round(cost, 2),
        'margin_impact': {
            'margin_percentage': round(margin_percentage, 1),
            'price_change': round(price_change, 2),
            'price_change_percent': round(price_change_percent, 1),
            'recommendation': 'increase' if price_change > 0 else 'decrease' if price_change < 0 else 'maintain'
        },
        'pricing_analysis': {
            'item_name': item.name,
            'item_id': item.id,
            'pricing_strategy': 'cost_plus_40pct',
            'confidence': 'medium'
        }
    }


def _analyze_event_pricing(event):
    """Analyze and suggest pricing for event."""
    current_quote = float(event.quoted_value or 0)
    total_cost = float(event.total_cost or 0)
    guest_count = event.guest_count or 1
    
    # Event pricing: 25-35% margin
    if total_cost > 0:
        suggested_price = total_cost * 1.3  # 30% margin
    else:
        # Estimate based on guest count
        cost_per_guest = 50000  # UGX
        estimated_cost = guest_count * cost_per_guest
        suggested_price = estimated_cost * 1.3
    
    margin_percentage = ((suggested_price - total_cost) / total_cost * 100) if total_cost > 0 else 30
    
    price_change = suggested_price - current_quote
    price_change_percent = (price_change / current_quote * 100) if current_quote > 0 else 0
    
    return {
        'success': True,
        'suggested_price': round(suggested_price, 2),
        'current_price': round(current_quote, 2),
        'cost': round(total_cost, 2),
        'margin_impact': {
            'margin_percentage': round(margin_percentage, 1),
            'price_change': round(price_change, 2),
            'price_change_percent': round(price_change_percent, 1),
            'recommendation': 'increase' if price_change > 0 else 'decrease' if price_change < 0 else 'maintain'
        },
        'pricing_analysis': {
            'event_title': event.title,
            'event_id': event.id,
            'guest_count': guest_count,
            'pricing_strategy': 'cost_plus_30pct',
            'confidence': 'high' if total_cost > 0 else 'medium'
        }
    }

