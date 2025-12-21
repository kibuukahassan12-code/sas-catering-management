"""
Pricing Advisor AI Service

Dynamic pricing recommendations based on market conditions.
"""
from flask import current_app
from decimal import Decimal
from sas_management.ai.registry import is_feature_enabled


def get_pricing_recommendations(item_id: int = None, category: str = None):
    """
    Get AI-powered pricing recommendations.
    
    Args:
        item_id: Menu item ID
        category: Item category
        
    Returns:
        Dictionary with pricing recommendations
    """
    # Check if feature is enabled
    if not is_feature_enabled("pricing_advisor"):
        return {
            "success": False,
            "error": "Pricing Advisor feature is disabled",
            "recommended_price": None,
            "market_analysis": {},
        }
    
    try:
        current_app.logger.info(f"Pricing Advisor accessed for item: {item_id}, category: {category}")
        
        recommended_price = None
        market_analysis = {}
        
        try:
            # Analyze pricing from similar items/quotes
            from sas_management.models import Quote, MenuItem
            
            if item_id:
                # Get menu item
                item = MenuItem.query.get(item_id)
                if item:
                    # Find similar items in quotes
                    quotes = Quote.query.filter(
                        Quote.status == "Accepted",
                        Quote.notes.contains(item.name) if item.name else True
                    ).limit(20).all()
                    
                    if quotes:
                        prices = []
                        for quote in quotes:
                            if quote.total_amount and quote.guest_count:
                                price_per_guest = float(quote.total_amount) / quote.guest_count
                                prices.append(price_per_guest)
                        
                        if prices:
                            avg_price = sum(prices) / len(prices)
                            recommended_price = avg_price * 1.1  # 10% markup
                            market_analysis = {
                                "average_market_price": avg_price,
                                "sample_size": len(prices),
                                "recommendation": "above_average" if recommended_price > avg_price else "at_market",
                            }
            
        except Exception as e:
            current_app.logger.warning(f"Error analyzing pricing: {e}")
        
        return {
            "success": True,
            "recommended_price": float(recommended_price) if recommended_price else None,
            "market_analysis": market_analysis,
            "confidence": "medium" if recommended_price else "low",
            "note": "Recommendations based on historical quote data" if recommended_price else "Insufficient data for pricing recommendations",
        }
        
    except Exception as e:
        current_app.logger.error(f"Pricing Advisor error: {e}")
        return {
            "success": False,
            "error": str(e),
            "recommended_price": None,
            "market_analysis": {},
        }

