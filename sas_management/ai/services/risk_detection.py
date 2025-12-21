"""
Risk Detection AI Service

Detects fraud flags and loss risks in transactions and operations.
"""
from flask import current_app
from datetime import date, timedelta


def run(payload, user):
    """
    Run Risk Detection AI service.
    
    Args:
        payload: dict with optional 'scan_type' ('transactions', 'inventory', 'all')
        user: Current user object
    
    Returns:
        dict: {
            'success': bool,
            'fraud_flags': list,
            'loss_risks': list,
            'risk_score': float,
            'error': str (if failed)
        }
    """
    try:
        scan_type = payload.get('scan_type', 'all')
        
        fraud_flags = []
        loss_risks = []
        
        if scan_type in ['transactions', 'all']:
            fraud_flags.extend(_scan_transactions())
            loss_risks.extend(_scan_financial_risks())
        
        if scan_type in ['inventory', 'all']:
            fraud_flags.extend(_scan_inventory())
            loss_risks.extend(_scan_inventory_risks())
        
        # Calculate overall risk score (0-100)
        risk_score = min(100, len(fraud_flags) * 10 + len(loss_risks) * 5)
        
        return {
            'success': True,
            'fraud_flags': fraud_flags,
            'loss_risks': loss_risks,
            'risk_score': risk_score,
            'scan_type': scan_type,
            'total_flags': len(fraud_flags),
            'total_risks': len(loss_risks)
        }
        
    except Exception as e:
        current_app.logger.exception(f"Risk Detection AI error: {e}")
        return {
            'success': False,
            'error': str(e),
            'fraud_flags': [],
            'loss_risks': [],
            'risk_score': 0.0
        }


def _scan_transactions():
    """Scan for transaction fraud flags."""
    flags = []
    
    try:
        from sas_management.models import Transaction, Event
        
        # Check for unusually large transactions
        recent_date = date.today() - timedelta(days=30)
        large_transactions = Transaction.query.filter(
            Transaction.date >= recent_date
        ).all()
        
        if large_transactions:
            amounts = [float(t.amount or 0) for t in large_transactions]
            if amounts:
                avg_amount = sum(amounts) / len(amounts)
                for trans in large_transactions:
                    amount = float(trans.amount or 0)
                    if amount > avg_amount * 3:  # 3x average
                        flags.append({
                            'type': 'unusually_large_transaction',
                            'severity': 'medium',
                            'description': f'Transaction {trans.id} is {amount:,.0f} UGX, significantly above average',
                            'transaction_id': trans.id
                        })
        
        # Check for events with zero or negative profit
        unprofitable_events = Event.query.filter(
            Event.profit <= 0,
            Event.date >= recent_date
        ).all()
        
        for event in unprofitable_events[:10]:  # Limit to 10
            flags.append({
                'type': 'unprofitable_event',
                'severity': 'low',
                'description': f'Event "{event.title}" has zero or negative profit',
                'event_id': event.id
            })
    
    except Exception as e:
        current_app.logger.warning(f"Transaction scan error: {e}")
    
    return flags


def _scan_financial_risks():
    """Scan for financial loss risks."""
    risks = []
    
    try:
        from sas_management.models import Event
        
        # Check for events with high costs but low revenue
        recent_date = date.today() - timedelta(days=90)
        events = Event.query.filter(
            Event.date >= recent_date
        ).all()
        
        for event in events:
            cost = float(event.total_cost or 0)
            revenue = float(event.quoted_value or 0)
            
            if cost > 0 and revenue > 0:
                margin = ((revenue - cost) / cost) * 100
                if margin < 10:  # Less than 10% margin
                    risks.append({
                        'type': 'low_margin_event',
                        'severity': 'medium',
                        'description': f'Event "{event.title}" has only {margin:.1f}% margin',
                        'event_id': event.id,
                        'margin_percent': round(margin, 1)
                    })
    
    except Exception as e:
        current_app.logger.warning(f"Financial risk scan error: {e}")
    
    return risks


def _scan_inventory():
    """Scan for inventory fraud flags."""
    flags = []
    
    try:
        from sas_management.models import InventoryItem
        
        # Check for items with negative stock (shouldn't happen)
        negative_stock = InventoryItem.query.filter(
            InventoryItem.stock_count < 0
        ).all()
        
        for item in negative_stock:
            flags.append({
                'type': 'negative_stock',
                'severity': 'high',
                'description': f'Item "{item.name}" has negative stock count: {item.stock_count}',
                'item_id': item.id
            })
        
        # Check for items with zero price but available
        zero_price_available = InventoryItem.query.filter(
            InventoryItem.unit_price_ugx == 0,
            InventoryItem.status == 'Available'
        ).all()
        
        for item in zero_price_available[:5]:  # Limit
            flags.append({
                'type': 'zero_price_item',
                'severity': 'low',
                'description': f'Item "{item.name}" is available but has zero price',
                'item_id': item.id
            })
    
    except Exception as e:
        current_app.logger.warning(f"Inventory scan error: {e}")
    
    return flags


def _scan_inventory_risks():
    """Scan for inventory loss risks."""
    risks = []
    
    try:
        from sas_management.models import InventoryItem
        
        # Check for items with very low stock
        low_stock_items = InventoryItem.query.filter(
            InventoryItem.stock_count <= 5,
            InventoryItem.status == 'Available'
        ).all()
        
        for item in low_stock_items[:20]:  # Limit to 20
            risks.append({
                'type': 'low_stock_risk',
                'severity': 'medium',
                'description': f'Item "{item.name}" is running low: {item.stock_count} units',
                'item_id': item.id,
                'stock_count': item.stock_count
            })
    
    except Exception as e:
        current_app.logger.warning(f"Inventory risk scan error: {e}")
    
    return risks

