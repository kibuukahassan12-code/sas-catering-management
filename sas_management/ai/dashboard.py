"""
AI Dashboard Logic

Business logic for the AI hub dashboard.
"""
from typing import Dict, List
from flask import current_app
from flask_login import current_user

from .registry import (
    get_feature_registry,
    get_enabled_features,
    get_features_by_category,
    is_feature_enabled,
)
from .state import get_all_features_state


def get_dashboard_data() -> Dict:
    """
    Get data for the AI dashboard.
    
    Returns:
        Dictionary with dashboard data including features, stats, etc.
    """
    ai_module_enabled = current_app.config.get("AI_MODULE_ENABLED", False)
    
    if not ai_module_enabled:
        return {
            "module_enabled": False,
            "features": [],
            "enabled_count": 0,
            "total_count": 0,
            "features_by_category": {},
        }
    
    registry = get_feature_registry()
    enabled_features = get_enabled_features()
    features_by_category = get_features_by_category()
    
    # Calculate statistics
    enabled_count = len(enabled_features)
    total_count = len(registry)
    
    # Log dashboard access
    from flask_login import current_user
    current_app.logger.info(
        f"AI dashboard accessed by user {current_user.email if current_user.is_authenticated else 'anonymous'}"
    )
    
    return {
        "module_enabled": True,
        "features": list(registry.values()),  # All features for admin view
        "enabled_features": enabled_features,
        "enabled_count": enabled_count,
        "total_count": total_count,
        "features_by_category": features_by_category,  # All features (admin can see all for toggling)
    }

