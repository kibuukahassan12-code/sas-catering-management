"""
Sales Forecasting AI Service

Predicts future revenue and sales with confidence scores.
"""
from flask import current_app
from datetime import date, timedelta
from statistics import mean


def run(payload, user):
    """
    Run Sales Forecasting AI service.
    
    Args:
        payload: dict with 'timeframe' (days) or 'start_date' and 'end_date'
        user: Current user object
    
    Returns:
        dict: {
            'success': bool,
            'predicted_revenue': float,
            'confidence_score': float,
            'forecast_breakdown': list,
            'error': str (if failed)
        }
    """
    try:
        from sas_management.models import Event, Transaction
        
        # Determine timeframe
        timeframe_days = int(payload.get('timeframe', 30))
        forecast_date = date.today() + timedelta(days=timeframe_days)
        
        # Get historical data (last 90 days)
        history_start = date.today() - timedelta(days=90)
        historical_events = Event.query.filter(
            Event.date >= history_start,
            Event.date <= date.today()
        ).all()
        
        # Calculate average daily revenue
        daily_revenues = []
        for event in historical_events:
            if event.quoted_value:
                daily_revenues.append(float(event.quoted_value))
        
        avg_daily_revenue = mean(daily_revenues) if daily_revenues else 0
        
        # Get upcoming events (already booked)
        upcoming_events = Event.query.filter(
            Event.date > date.today(),
            Event.date <= forecast_date
        ).all()
        
        confirmed_revenue = sum(float(e.quoted_value or 0) for e in upcoming_events)
        
        # Predict additional revenue based on historical patterns
        days_without_events = timeframe_days - len(upcoming_events)
        predicted_additional = avg_daily_revenue * days_without_events * 0.3  # 30% probability
        
        predicted_revenue = confirmed_revenue + predicted_additional
        
        # Calculate confidence based on data quality
        confidence_score = min(0.95, max(0.5, len(historical_events) / 30))  # More data = higher confidence
        
        # Forecast breakdown
        forecast_breakdown = [
            {
                'period': 'Confirmed Bookings',
                'revenue': confirmed_revenue,
                'confidence': 1.0
            },
            {
                'period': 'Predicted Additional',
                'revenue': predicted_additional,
                'confidence': confidence_score * 0.7
            }
        ]
        
        return {
            'success': True,
            'predicted_revenue': predicted_revenue,
            'confidence_score': confidence_score,
            'forecast_breakdown': forecast_breakdown,
            'timeframe_days': timeframe_days,
            'forecast_date': forecast_date.isoformat(),
            'historical_data_points': len(historical_events),
            'confirmed_bookings': len(upcoming_events)
        }
        
    except Exception as e:
        current_app.logger.exception(f"Sales Forecasting AI error: {e}")
        return {
            'success': False,
            'error': str(e),
            'predicted_revenue': 0.0,
            'confidence_score': 0.0,
            'forecast_breakdown': []
        }

