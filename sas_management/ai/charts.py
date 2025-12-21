"""
SAS AI Chart Data Generator - Creates Chart.js compatible data.
"""
from sqlalchemy import func
from datetime import datetime, timedelta, date
from sas_management.models import db

# Safe model imports
try:
    from sas_management.models import InventoryItem, AccountingPayment, Event
except Exception:
    InventoryItem = None
    AccountingPayment = None
    Event = None


def inventory_chart(days: int = 30) -> dict:
    """
    Generate inventory chart data.
    
    Returns:
        Chart.js compatible data structure
    """
    if not InventoryItem:
        return None
    
    try:
        # Get inventory by category
        categories = db.session.query(
            InventoryItem.category,
            func.count(InventoryItem.id).label('count')
        ).group_by(InventoryItem.category).all()
        
        labels = [cat[0] or "Uncategorized" for cat in categories]
        counts = [cat[1] for cat in categories]
        
        # Get low stock items
        low_stock = InventoryItem.query.filter(
            InventoryItem.stock_count <= 10
        ).count()
        
        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Items by Category",
                    "data": counts,
                    "backgroundColor": "rgba(246, 188, 56, 0.6)",
                    "borderColor": "rgba(246, 188, 56, 1)",
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": f"Inventory Overview (Low Stock: {low_stock} items)"
                    }
                }
            }
        }
    except Exception as e:
        import logging
        logger = logging.getLogger("sas_ai")
        logger.error(f"Error generating inventory chart: {e}", exc_info=True)
        return None


def revenue_chart(days: int = 30) -> dict:
    """
    Generate revenue chart data for last N days.
    
    Returns:
        Chart.js compatible data structure
    """
    if not AccountingPayment:
        return None
    
    try:
        # Get daily revenue for last N days
        cutoff_date = date.today() - timedelta(days=days)
        
        daily_revenue = db.session.query(
            AccountingPayment.date,
            func.sum(AccountingPayment.amount).label('total')
        ).filter(
            AccountingPayment.date >= cutoff_date
        ).group_by(AccountingPayment.date).order_by(AccountingPayment.date).all()
        
        labels = [str(d[0]) for d in daily_revenue]
        amounts = [float(d[1]) for d in daily_revenue]
        
        # If no data, return empty chart
        if not labels:
            return {
                "type": "line",
                "data": {
                    "labels": ["No data"],
                    "datasets": [{
                        "label": "Revenue",
                        "data": [0],
                        "borderColor": "rgba(246, 188, 56, 1)",
                        "backgroundColor": "rgba(246, 188, 56, 0.1)"
                    }]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {
                            "display": True,
                            "text": "Revenue Trend (Last 30 Days)"
                        }
                    }
                }
            }
        
        return {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Daily Revenue (UGX)",
                    "data": amounts,
                    "borderColor": "rgba(246, 188, 56, 1)",
                    "backgroundColor": "rgba(246, 188, 56, 0.1)",
                    "fill": True,
                    "tension": 0.4
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": f"Revenue Trend (Last {days} Days)"
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            }
        }
    except Exception as e:
        import logging
        logger = logging.getLogger("sas_ai")
        logger.error(f"Error generating inventory chart: {e}", exc_info=True)
        return None


def events_chart(days: int = 30) -> dict:
    """
    Generate events chart data.
    
    Returns:
        Chart.js compatible data structure
    """
    if not Event:
        return None
    
    try:
        # Get events by status
        statuses = db.session.query(
            Event.status,
            func.count(Event.id).label('count')
        ).group_by(Event.status).all()
        
        labels = [s[0] or "Unknown" for s in statuses]
        counts = [s[1] for s in statuses]
        
        return {
            "type": "doughnut",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Events by Status",
                    "data": counts,
                    "backgroundColor": [
                        "rgba(246, 188, 56, 0.6)",
                        "rgba(16, 185, 129, 0.6)",
                        "rgba(239, 68, 68, 0.6)",
                        "rgba(59, 130, 246, 0.6)"
                    ]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "Events Overview"
                    }
                }
            }
        }
    except Exception as e:
        import logging
        logger = logging.getLogger("sas_ai")
        logger.error(f"Error generating inventory chart: {e}", exc_info=True)
        return None

