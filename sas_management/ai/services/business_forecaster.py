"""
Business Forecaster AI Service

Predict future business trends and performance.
"""
from flask import current_app
from datetime import datetime, timedelta
from decimal import Decimal
from sas_management.ai.registry import is_feature_enabled


def forecast_business_metrics(horizon_days: int = 90, metrics: list = None):
    """
    Forecast business metrics for the specified horizon.
    
    Args:
        horizon_days: Number of days to forecast ahead
        metrics: List of metrics to forecast (revenue, costs, etc.)
        
    Returns:
        Dictionary with business forecasts
    """
    # Check if feature is enabled
    if not is_feature_enabled("business_forecaster"):
        return {
            "success": False,
            "error": "Business Forecaster feature is disabled",
            "revenue_forecast": [],
            "cost_forecast": [],
        }
    
    try:
        current_app.logger.info(f"Business Forecaster accessed for horizon: {horizon_days} days")
        
        revenue_forecast = []
        cost_forecast = []
        trends = []
        
        try:
            from sas_management.models import Event, Quote, Invoice
            
            # Analyze historical data
            lookback_days = min(horizon_days * 2, 365)  # Look back up to 2x horizon or 1 year
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            # Calculate average daily revenue
            total_revenue = Decimal("0")
            day_count = 0
            
            quotes = Quote.query.filter(
                Quote.created_at >= cutoff_date,
                Quote.status == "Accepted"
            ).all()
            
            for quote in quotes:
                if quote.total_amount and quote.created_at:
                    total_revenue += Decimal(str(quote.total_amount))
                    day_count += 1
            
            if day_count > 0:
                avg_daily_revenue = float(total_revenue) / lookback_days
                
                # Simple linear forecast
                for i in range(0, horizon_days, 7):  # Weekly forecasts
                    forecast_date = datetime.utcnow() + timedelta(days=i)
                    forecast_revenue = avg_daily_revenue * 7  # Weekly revenue
                    
                    revenue_forecast.append({
                        "date": forecast_date.strftime("%Y-%m-%d"),
                        "revenue": forecast_revenue,
                        "confidence": "medium" if day_count >= 30 else "low",
                    })
                
                trends.append({
                    "type": "revenue_trend",
                    "direction": "stable",
                    "message": f"Average daily revenue: {avg_daily_revenue:,.0f} UGX",
                })
            
            # Forecast costs (assume 70% of revenue as COGS)
            for rev_item in revenue_forecast:
                cost_forecast.append({
                    "date": rev_item["date"],
                    "cost": rev_item["revenue"] * 0.7,
                    "confidence": rev_item["confidence"],
                })
        
        except Exception as e:
            current_app.logger.warning(f"Error forecasting business metrics: {e}")
        
        return {
            "success": True,
            "revenue_forecast": revenue_forecast,
            "cost_forecast": cost_forecast,
            "trends": trends,
            "horizon_days": horizon_days,
            "confidence": "medium" if revenue_forecast else "low",
            "note": f"Forecast based on {day_count} data points over {lookback_days} days" if day_count > 0 else "Insufficient data for forecasting",
        }
        
    except Exception as e:
        current_app.logger.error(f"Business Forecaster error: {e}")
        return {
            "success": False,
            "error": str(e),
            "revenue_forecast": [],
            "cost_forecast": [],
        }

