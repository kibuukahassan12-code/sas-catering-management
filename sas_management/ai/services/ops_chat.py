"""
Operations Chat Assistant AI Service

AI chat assistant for operational questions and guidance.
"""
from flask import current_app
from sas_management.ai.feature_model import is_ai_feature_enabled


def chat_with_assistant(message: str, context: dict = None):
    """
    Chat with the operations AI assistant.
    
    Args:
        message: User's message
        context: Additional context (event_id, etc.)
        
    Returns:
        Dictionary with assistant response
    """
    # Check if feature is enabled (DB-backed)
    if not is_ai_feature_enabled("operations_chat_assistant"):
        return {
            "success": False,
            "error": "Feature disabled by admin",
            "response": "Operations Chat Assistant is currently disabled by your administrator.",
        }
    
    try:
        current_app.logger.info(f"Ops Chat accessed with message length: {len(message) if message else 0}")
        
        message_lower = (message or "").lower()
        response = ""
        suggestions = []
        
        # Simple rule-based responses
        if any(word in message_lower for word in ["event", "plan", "planning"]):
            response = "For event planning assistance, I can help you with:\n- Staff role recommendations\n- Checklist items\n- Cost estimates\n\nUse the Event Planning Assistant feature for detailed suggestions."
            suggestions = ["View Event Planning Assistant", "Create new event"]
        
        elif any(word in message_lower for word in ["quote", "quotation", "pricing"]):
            response = "For quotation and pricing help:\n- Use Quotation AI for intelligent quote generation\n- Pricing Advisor provides dynamic pricing recommendations\n\nBoth features analyze historical data to provide suggestions."
            suggestions = ["View Quotation AI", "View Pricing Advisor"]
        
        elif any(word in message_lower for word in ["profit", "margin", "cost"]):
            response = "For profit analysis:\n- Profit Analyzer identifies optimization opportunities\n- Analyzes margins across events and services\n\nAccess it from the SAS AI dashboard."
            suggestions = ["View Profit Analyzer"]
        
        elif any(word in message_lower for word in ["inventory", "stock", "shortage"]):
            response = "For inventory management:\n- Inventory Predictor forecasts needs and shortages\n- Based on upcoming events and consumption patterns\n\nCheck the Inventory Predictor feature for predictions."
            suggestions = ["View Inventory Predictor"]
        
        elif any(word in message_lower for word in ["help", "how", "what"]):
            response = "I'm the Operations Chat Assistant. I can help with:\n- Event planning guidance\n- System navigation\n- Feature recommendations\n\nAsk me about any operational topic, or browse the SAS AI dashboard for specific features."
            suggestions = ["View AI Dashboard", "Browse Features"]
        
        else:
            response = "I understand you're asking about operations. For specific assistance, I recommend:\n- Event Planning Assistant for event-related questions\n- Quotation AI for pricing and quotes\n- Profit Analyzer for financial analysis\n\nYou can also browse all AI features from the SAS AI dashboard."
            suggestions = ["View AI Dashboard"]
        
        return {
            "success": True,
            "response": response,
            "suggestions": suggestions,
            "confidence": "medium",
        }
        
    except Exception as e:
        current_app.logger.error(f"Ops Chat error: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "I'm sorry, I encountered an error. Please try again or contact support.",
        }

