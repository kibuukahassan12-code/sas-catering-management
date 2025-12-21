"""
Quotation AI Service

AI-powered quotation generation and pricing recommendations.
"""
from flask import current_app
from sas_management.ai.registry import is_feature_enabled


def generate_quotation_suggestions(client_id: int = None, event_type: str = None):
    """
    Generate AI-powered quotation suggestions.
    
    Args:
        client_id: Client ID
        event_type: Type of event
        
    Returns:
        Dictionary with quotation suggestions
    """
    # Check if feature is enabled
    if not is_feature_enabled("quotation_ai"):
        return {
            "success": False,
            "error": "Quotation AI feature is disabled",
            "suggested_items": [],
            "pricing_recommendations": [],
        }
    
    try:
        current_app.logger.info(f"Quotation AI accessed for client: {client_id}, event: {event_type}")
        
        # Analyze past quotations for similar events/clients
        suggested_items = []
        pricing_recommendations = []
        
        try:
            from sas_management.models import Quote, Client
            
            # Get similar past quotations
            query = Quote.query.filter(Quote.status == "Accepted")
            
            if client_id:
                query = query.filter(Quote.client_id == client_id)
            
            if event_type:
                # Try to match event type from quote notes or title
                query = query.filter(
                    Quote.notes.contains(event_type) | Quote.title.contains(event_type)
                )
            
            similar_quotes = query.order_by(Quote.created_at.desc()).limit(10).all()
            
            if similar_quotes:
                # Analyze common items and pricing
                item_frequency = {}
                total_value = 0
                count = 0
                
                for quote in similar_quotes:
                    if quote.total_amount:
                        total_value += float(quote.total_amount)
                        count += 1
                    
                    # Extract items from quote (if available)
                    if quote.notes:
                        # Simple heuristic: look for common menu items
                        notes_lower = quote.notes.lower()
                        common_items = ["chicken", "beef", "rice", "salad", "dessert", "drinks"]
                        for item in common_items:
                            if item in notes_lower:
                                item_frequency[item] = item_frequency.get(item, 0) + 1
                
                # Generate suggestions
                for item, freq in sorted(item_frequency.items(), key=lambda x: x[1], reverse=True)[:5]:
                    suggested_items.append({
                        "item": item.title(),
                        "frequency": freq,
                        "recommendation": "high" if freq >= 3 else "medium",
                    })
                
                if count > 0:
                    avg_value = total_value / count
                    pricing_recommendations.append({
                        "type": "average_quote_value",
                        "value": avg_value,
                        "confidence": "medium" if count >= 3 else "low",
                        "note": f"Based on {count} similar accepted quotations",
                    })
        
        except Exception as e:
            current_app.logger.warning(f"Error analyzing quotations: {e}")
        
        return {
            "success": True,
            "suggested_items": suggested_items,
            "pricing_recommendations": pricing_recommendations,
            "confidence": "medium" if suggested_items or pricing_recommendations else "low",
            "note": "Suggestions based on historical quotation data" if suggested_items or pricing_recommendations else "Insufficient data for recommendations",
        }
        
    except Exception as e:
        current_app.logger.error(f"Quotation AI error: {e}")
        return {
            "success": False,
            "error": str(e),
            "suggested_items": [],
            "pricing_recommendations": [],
        }

