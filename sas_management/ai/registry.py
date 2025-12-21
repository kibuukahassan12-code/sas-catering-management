"""
AI Feature Registry

CANONICAL registry for all AI features in the SAS Management System.
This is the SINGLE SOURCE OF TRUTH for AI feature definitions.
Each feature defines its metadata, integration point, enabled status, and service handler.
"""
from typing import Dict, List, Optional, Callable
from flask import current_app


# Feature metadata definitions - SINGLE SOURCE OF TRUTH
FEATURE_DEFINITIONS = {
    "event_planner": {
        "name": "Event Planning Assistant",
        "description": "AI-powered event planning suggestions based on historical data. Provides staff role recommendations, checklist items, and cost estimates.",
        "business_value": "Revenue",
        "module_integration": "service",
        "icon": "📅",
        "category": "Operations",
        "service_handler": "sas_management.ai.services.event_planner.get_event_planning_suggestions",
    },
    "quotation_ai": {
        "name": "Quotation AI",
        "description": "Intelligent quotation generation with pricing recommendations and competitive analysis.",
        "business_value": "Revenue",
        "module_integration": "quotes",
        "icon": "💰",
        "category": "Sales",
        "service_handler": "sas_management.ai.services.quotation_ai.generate_quotation_suggestions",
    },
    "profit_analyzer": {
        "name": "Profit Analyzer",
        "description": "Analyze profit margins across events, menu items, and services. Identify optimization opportunities.",
        "business_value": "Cost",
        "module_integration": "profitability",
        "icon": "📊",
        "category": "Finance",
        "service_handler": "sas_management.ai.services.profit_analyzer.analyze_profit_opportunities",
    },
    "pricing_advisor": {
        "name": "Pricing Advisor",
        "description": "Dynamic pricing recommendations based on market conditions, costs, and demand patterns.",
        "business_value": "Revenue",
        "module_integration": "quotes",
        "icon": "💵",
        "category": "Sales",
        "service_handler": "sas_management.ai.services.pricing_advisor.get_pricing_recommendations",
    },
    "staff_coach": {
        "name": "Staff Performance Coach",
        "description": "AI-powered staff performance analysis and personalized coaching recommendations.",
        "business_value": "Cost",
        "module_integration": "hr",
        "icon": "👥",
        "category": "HR",
        "service_handler": "sas_management.ai.services.staff_coach.get_staff_coaching_recommendations",
    },
    "inventory_predictor": {
        "name": "Inventory Predictor",
        "description": "Predict inventory needs and shortages using historical consumption patterns and event forecasts.",
        "business_value": "Cost",
        "module_integration": "inventory",
        "icon": "📦",
        "category": "Operations",
        "service_handler": "sas_management.ai.services.inventory_predictor.predict_inventory_needs",
    },
    "client_analyzer": {
        "name": "Client Analyzer",
        "description": "Analyze client behavior, preferences, and lifetime value. Identify upsell opportunities.",
        "business_value": "Revenue",
        "module_integration": "crm",
        "icon": "👤",
        "category": "Sales",
        "service_handler": "sas_management.ai.services.client_analyzer.analyze_client",
    },
    "compliance_monitor": {
        "name": "Compliance Monitor",
        "description": "Monitor food safety, hygiene, and regulatory compliance. Alert on potential violations.",
        "business_value": "Risk",
        "module_integration": "food_safety",
        "icon": "⚠️",
        "category": "Compliance",
        "service_handler": "sas_management.ai.services.compliance_monitor.check_compliance_status",
    },
    "ops_chat": {
        "name": "Operations Chat Assistant",
        "description": "AI chat assistant for operational questions, event planning help, and system guidance.",
        "business_value": "Efficiency",
        "module_integration": "core",
        "icon": "💬",
        "category": "Operations",
        "service_handler": "sas_management.ai.services.ops_chat.chat_with_assistant",
    },
    "business_forecaster": {
        "name": "Business Forecaster",
        "description": "Predict future revenue, costs, and business trends using historical data and market analysis.",
        "business_value": "Revenue",
        "module_integration": "bi",
        "icon": "🔮",
        "category": "Finance",
        "service_handler": "sas_management.ai.services.business_forecaster.forecast_business_metrics",
    },
    "ai_chat": {
        "name": "SAS AI Chat",
        "description": "Premium AI chat assistant for system queries, business intelligence, and intelligent assistance.",
        "business_value": "Efficiency",
        "module_integration": "core",
        "icon": "💬",
        "category": "Operations",
        "service_handler": "sas_management.ai.services.ai_chat.process_chat_message",
    },
}


def get_feature_registry() -> Dict[str, Dict]:
    """
    Get the complete feature registry with enabled status.
    Registry is declarative metadata only - enabled state comes from ai.state.
    
    Returns:
        Dictionary mapping feature keys to feature metadata with 'enabled' status
    """
    from sas_management.ai.state import is_enabled
    
    registry = {}
    
    for feature_key, feature_def in FEATURE_DEFINITIONS.items():
        # Get enabled state dynamically from ai.state
        feature_enabled = is_enabled(feature_key)
        
        registry[feature_key] = {
            **feature_def,
            "key": feature_key,
            "enabled": feature_enabled,
        }
    
    return registry


def get_enabled_features() -> List[Dict]:
    """
    Get list of enabled AI features only.
    
    Returns:
        List of feature dictionaries
    """
    registry = get_feature_registry()
    return [feature for feature in registry.values() if feature["enabled"]]


def is_feature_enabled(feature_key: str) -> bool:
    """
    Check if a specific AI feature is enabled.
    Delegates to ai.state for runtime state.
    
    Args:
        feature_key: Key of the feature to check
        
    Returns:
        True if feature is enabled, False otherwise
    """
    from sas_management.ai.state import is_enabled
    return is_enabled(feature_key)


def get_feature_by_key(feature_key: str) -> Optional[Dict]:
    """
    Get a specific feature by its key.
    
    Args:
        feature_key: Key of the feature
        
    Returns:
        Feature dictionary or None if not found
    """
    registry = get_feature_registry()
    return registry.get(feature_key)


def get_features_by_category() -> Dict[str, List[Dict]]:
    """
    Get features grouped by category.
    
    Returns:
        Dictionary mapping category names to lists of features
    """
    registry = get_feature_registry()
    by_category = {}
    
    for feature in registry.values():
        category = feature.get("category", "Other")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(feature)
    
    return by_category

