"""
Event Planning AI Service

Integrates with the Event Service module to provide AI-powered planning assistance.
"""
from flask import current_app
from sas_management.ai.feature_model import is_ai_feature_enabled


def get_event_planning_suggestions(event_type: str = None, guest_count: int = None):
    """
    Get AI-powered event planning suggestions.
    
    This service integrates with sas_management.service.ai_planner.
    
    Args:
        event_type: Type of event
        guest_count: Number of guests
        
    Returns:
        Dictionary with planning suggestions
    """
    # Check if feature is enabled (DB-backed)
    if not is_ai_feature_enabled("event_planning_assistant"):
        return {
            "success": False,
            "error": "Feature disabled by admin",
            "staff_suggestions": [],
            "checklist": [],
            "estimated_cost": 0.0,
            "confidence_note": "Event Planning Assistant is disabled by your administrator.",
        }
    
    try:
        from sas_management.service.ai_planner import generate_plan
        from datetime import date
        
        result = generate_plan(
            event_type=event_type,
            guest_count=guest_count,
            event_date=None,
        )
        
        # Add success flag
        result["success"] = True
        
        current_app.logger.info(f"Event planning AI used for type: {event_type}, guests: {guest_count}")
        return result
    except Exception as e:
        current_app.logger.warning(f"Event planning AI error: {e}")
        return {
            "success": False,
            "error": str(e),
            "staff_suggestions": [],
            "checklist": [],
            "estimated_cost": 0.0,
            "confidence_note": "Service unavailable",
        }

