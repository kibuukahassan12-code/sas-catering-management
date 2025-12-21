"""
Profit Analyzer AI Service

Analyze profit margins and identify optimization opportunities.
"""
from flask import current_app
from datetime import datetime, timedelta
from decimal import Decimal
from sas_management.ai.registry import is_feature_enabled


def analyze_profit_opportunities(timeframe: str = "30d"):
    """
    Analyze profit opportunities across the business.
    
    Args:
        timeframe: Time period to analyze (e.g., "30d", "90d", "1y")
        
    Returns:
        Dictionary with profit analysis results
    """
    # Check if feature is enabled
    if not is_feature_enabled("profit_analyzer"):
        return {
            "success": False,
            "error": "Profit Analyzer feature is disabled",
            "opportunities": [],
            "low_margin_items": [],
            "recommendations": [],
        }
    
    try:
        current_app.logger.info(f"Profit Analyzer accessed for timeframe: {timeframe}")
        
        # Parse timeframe
        days = 30
        if timeframe.endswith("d"):
            days = int(timeframe[:-1])
        elif timeframe.endswith("y"):
            days = int(timeframe[:-1]) * 365
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        opportunities = []
        low_margin_items = []
        recommendations = []
        
        try:
            from sas_management.models import Event, Invoice
            
            # Analyze events for profit margins
            events = Event.query.filter(Event.created_at >= cutoff_date).all()
            
            total_revenue = Decimal("0")
            total_cogs = Decimal("0")
            event_count = 0
            
            for event in events:
                try:
                    # Get revenue (from invoices or quote)
                    revenue = Decimal("0")
                    if hasattr(event, "quote") and event.quote and event.quote.total_amount:
                        revenue = Decimal(str(event.quote.total_amount))
                    elif hasattr(event, "invoices"):
                        for inv in event.invoices:
                            if inv.amount_paid:
                                revenue += Decimal(str(inv.amount_paid))
                    
                    # Get COGS
                    cogs = Decimal("0")
                    if hasattr(event, "actual_cogs_ugx") and event.actual_cogs_ugx:
                        cogs = Decimal(str(event.actual_cogs_ugx))
                    
                    if revenue > 0:
                        total_revenue += revenue
                        total_cogs += cogs
                        event_count += 1
                        
                        # Calculate margin
                        margin = ((revenue - cogs) / revenue * 100) if revenue > 0 else 0
                        
                        if margin < 20:  # Low margin threshold
                            low_margin_items.append({
                                "event_id": event.id,
                                "title": event.title or "Untitled Event",
                                "margin": float(margin),
                                "revenue": float(revenue),
                                "cogs": float(cogs),
                            })
                except Exception:
                    continue
            
            # Generate recommendations
            if event_count > 0:
                avg_margin = ((total_revenue - total_cogs) / total_revenue * 100) if total_revenue > 0 else 0
                
                if avg_margin < 25:
                    recommendations.append({
                        "type": "improve_margins",
                        "priority": "high",
                        "message": f"Average profit margin is {avg_margin:.1f}%. Consider reviewing pricing or reducing costs.",
                    })
                
                if len(low_margin_items) > event_count * 0.3:  # More than 30% have low margins
                    recommendations.append({
                        "type": "review_pricing",
                        "priority": "medium",
                        "message": f"{len(low_margin_items)} events have margins below 20%. Review pricing strategy.",
                    })
                
                opportunities.append({
                    "type": "cost_reduction",
                    "description": f"Potential to improve margins by {25 - avg_margin:.1f}%",
                    "impact": "high" if avg_margin < 20 else "medium",
                })
        
        except Exception as e:
            current_app.logger.warning(f"Error analyzing profits: {e}")
        
        return {
            "success": True,
            "opportunities": opportunities,
            "low_margin_items": low_margin_items[:10],  # Limit to top 10
            "recommendations": recommendations,
            "timeframe": timeframe,
            "note": f"Analysis based on {event_count} events in the last {days} days" if event_count > 0 else "Insufficient data for analysis",
        }
        
    except Exception as e:
        current_app.logger.error(f"Profit Analyzer error: {e}")
        return {
            "success": False,
            "error": str(e),
            "opportunities": [],
            "low_margin_items": [],
            "recommendations": [],
        }

