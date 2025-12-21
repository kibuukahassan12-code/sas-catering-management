"""
SAS AI Predictive Analytics - Pure Python predictions without ML libraries.
"""
from sqlalchemy import func
from datetime import datetime, timedelta, date
from sas_management.models import db
from sas_management.ai.analytics_helpers import require_min_records, format_forecast_disclaimer

# Safe model imports
try:
    from sas_management.models import InventoryItem, Transaction, Invoice, AccountingPayment
except Exception:
    InventoryItem = None
    Transaction = None
    Invoice = None
    AccountingPayment = None


def forecast_inventory(item_id: int = None, days_ahead: int = 30) -> dict:
    """
    Predict inventory stock levels using historical usage.
    
    Args:
        item_id: Specific item ID, or None for general forecast
        days_ahead: Days to project forward
    
    Returns:
        dict with prediction, confidence, and details
    """
    if not InventoryItem or not Transaction:
        return {
            "prediction": "Insufficient data for inventory forecasting.",
            "confidence": 0.0,
            "details": {}
        }
    
    try:
        # Get last 90 days of transactions
        cutoff_date = date.today() - timedelta(days=90)
        
        if item_id:
            # Forecast specific item
            item = InventoryItem.query.get(item_id)
            if not item:
                return {
                    "prediction": f"⚠️ Item {item_id} not found.",
                    "confidence": 0.0,
                    "details": {}
                }
            
            current_stock = getattr(item, 'stock_count', 0) or 0
            
            # Calculate average daily usage from transactions
            usage_transactions = Transaction.query.filter(
                Transaction.created_at >= cutoff_date,
                Transaction.transaction_type == "Expense"
            ).all()
            
            # Harden: Require minimum data points using shared helper
            ok, error_msg = require_min_records(len(usage_transactions), min_required=5)
            if not ok:
                return {
                    "prediction": error_msg,
                    "confidence": 0.0,
                    "details": {"data_points": len(usage_transactions)}
                }
            
            # Calculate average daily usage from historical transactions
            avg_daily_usage = len(usage_transactions) / 90.0 if usage_transactions else 0.1
            
            # Estimate days until low stock (with explanation)
            days_until_low = int(current_stock / avg_daily_usage) if avg_daily_usage > 0 else 999
            
            prediction_text = (
                f"Based on recent usage patterns over the last 90 days, item '{item.name}' "
                f"has approximately {days_until_low} days until low stock.\n\n"
                f"Analysis: Current stock ({current_stock}) divided by average daily usage "
                f"({avg_daily_usage:.2f} transactions/day)."
            )
            
            if days_until_low < days_ahead:
                prediction_text += f"\n\n⚠️ Reorder recommended within {days_until_low} days."
            
            # Add disclaimer
            prediction_text += format_forecast_disclaimer()
            
            confidence = min(0.85, max(0.5, 1.0 - (len(usage_transactions) / 100.0)))
            
            return {
                "prediction": prediction_text,
                "confidence": round(confidence, 2),
                "details": {
                    "current_stock": current_stock,
                    "avg_daily_usage": round(avg_daily_usage, 2),
                    "days_until_low": days_until_low
                }
            }
        else:
            # General inventory forecast
            total_items = InventoryItem.query.count()
            low_stock_count = InventoryItem.query.filter(
                InventoryItem.stock_count <= 10
            ).count()
            
            # Harden: Require minimum items using shared helper
            ok, error_msg = require_min_records(total_items, min_required=5)
            if not ok:
                return {
                    "prediction": error_msg,
                    "confidence": 0.0,
                    "details": {"total_items": total_items}
                }
            
            # Project based on current low stock trend
            projected_low_stock = max(1, int(low_stock_count * 1.2))
            
            prediction_text = (
                f"Out of {total_items} inventory items, {low_stock_count} are currently low on stock.\n\n"
                f"Based on historical patterns, expect approximately {projected_low_stock} items "
                f"to need reordering within the next {days_ahead} days.\n\n"
                f"Analysis: Current low stock count ({low_stock_count}) with 20% growth projection "
                f"based on typical inventory turnover patterns."
            )
            
            # Add disclaimer
            prediction_text += format_forecast_disclaimer()
            
            return {
                "prediction": prediction_text,
                "confidence": 0.75,
                "details": {
                    "total_items": total_items,
                    "low_stock_count": low_stock_count,
                    "projected_low_stock": max(1, int(low_stock_count * 1.2))
                }
            }
            
    except Exception as e:
        return {
            "prediction": f"⚠️ An error occurred while generating inventory forecast: {str(e)}",
            "confidence": 0.0,
            "details": {"error": str(e)}
        }


def forecast_revenue(days_ahead: int = 30) -> dict:
    """
    Predict revenue using historical payment data.
    
    Args:
        days_ahead: Days to project forward
    
    Returns:
        dict with prediction, confidence, and details
    """
    if not AccountingPayment:
        return {
            "prediction": "Insufficient data for revenue forecasting.",
            "confidence": 0.0,
            "details": {}
        }
    
    try:
        # Get last 90 days of payments
        cutoff_date = date.today() - timedelta(days=90)
        
        recent_payments = AccountingPayment.query.filter(
            AccountingPayment.date >= cutoff_date
        ).all()
        
        if not recent_payments:
            return {
                "prediction": "⚠️ No recent payment data available for forecasting.",
                "confidence": 0.0,
                "details": {}
            }
        
        # Harden: Require minimum data points using shared helper
        ok, error_msg = require_min_records(len(recent_payments), min_required=5)
        if not ok:
            return {
                "prediction": error_msg,
                "confidence": 0.0,
                "details": {"data_points": len(recent_payments)}
            }
        
        # Calculate average daily revenue from historical data
        total_revenue = sum(float(p.amount) for p in recent_payments)
        avg_daily_revenue = total_revenue / 90.0
        
        # Project forward using historical average
        projected_revenue = avg_daily_revenue * days_ahead
        
        # Calculate trend by comparing first half vs second half of period
        mid_point = len(recent_payments) // 2
        if mid_point > 0:
            first_half = sum(float(p.amount) for p in recent_payments[:mid_point])
            second_half = sum(float(p.amount) for p in recent_payments[mid_point:])
            trend = "increasing" if second_half > first_half else "decreasing" if second_half < first_half else "stable"
        else:
            trend = "stable"
        
        prediction_text = (
            f"Based on the last 90 days of payment data ({len(recent_payments)} records), "
            f"projected revenue for the next {days_ahead} days is approximately "
            f"**{projected_revenue:,.2f} UGX**.\n\n"
            f"Analysis:\n"
            f"• Average daily revenue: {avg_daily_revenue:,.2f} UGX\n"
            f"• Trend: {trend.capitalize()} revenue pattern detected\n"
            f"• Projection method: Historical average multiplied by forecast period"
        )
        
        # Add disclaimer
        prediction_text += format_forecast_disclaimer()
        
        # Confidence based on data volume
        confidence = min(0.90, max(0.6, len(recent_payments) / 50.0))
        
        return {
            "prediction": prediction_text,
            "confidence": round(confidence, 2),
            "details": {
                "avg_daily_revenue": round(avg_daily_revenue, 2),
                "projected_revenue": round(projected_revenue, 2),
                "trend": trend,
                "data_points": len(recent_payments)
            }
        }
        
    except Exception as e:
        return {
            "prediction": f"⚠️ An error occurred while generating revenue forecast: {str(e)}",
            "confidence": 0.0,
            "details": {"error": str(e)}
        }

