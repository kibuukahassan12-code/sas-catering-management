"""
SAS Branding

Centralized branding constants and helpers for SAS AI module.
"""
from flask import url_for


# SAS Brand Colors
SAS_PRIMARY = "#F26822"  # SAS Orange
SAS_SECONDARY = "#2D5016"  # SAS Green
SAS_DARK = "#1a1a1a"
SAS_LIGHT = "#f5f5f5"
SAS_SUCCESS = "#10b981"
SAS_WARNING = "#f59e0b"
SAS_ERROR = "#ef4444"
SAS_INFO = "#3b82f6"

# Business Value Colors
VALUE_COLORS = {
    "Revenue": SAS_PRIMARY,  # Orange
    "Cost": SAS_WARNING,    # Amber
    "Risk": SAS_ERROR,      # Red
    "Efficiency": SAS_INFO, # Blue
}

# Feature Icons
FEATURE_ICONS = {
    "event_planner": "📅",
    "quotation_ai": "💰",
    "profit_analyzer": "📊",
    "pricing_advisor": "💵",
    "staff_coach": "👥",
    "inventory_predictor": "📦",
    "client_analyzer": "👤",
    "compliance_monitor": "⚠️",
    "ops_chat": "💬",
    "business_forecaster": "🔮",
}


def get_sas_logo_url():
    """
    Get SAS logo URL with graceful fallback.
    
    Returns:
        str: URL to logo or None if not available
    """
    try:
        return url_for("static", filename="images/ssas_logo.png")
    except Exception:
        return None


def get_brand_css():
    """
    Get inline CSS for SAS branding.
    
    Returns:
        str: CSS string
    """
    return f"""
    .sas-ai-primary {{ color: {SAS_PRIMARY}; }}
    .sas-ai-bg-primary {{ background-color: {SAS_PRIMARY}; }}
    .sas-ai-border-primary {{ border-color: {SAS_PRIMARY}; }}
    .sas-ai-secondary {{ color: {SAS_SECONDARY}; }}
    .sas-ai-bg-secondary {{ background-color: {SAS_SECONDARY}; }}
    """


def get_value_color(business_value: str) -> str:
    """
    Get color for business value tag.
    
    Args:
        business_value: One of "Revenue", "Cost", "Risk", "Efficiency"
        
    Returns:
        str: Hex color code
    """
    return VALUE_COLORS.get(business_value, SAS_INFO)


def get_feature_icon(feature_key: str) -> str:
    """
    Get icon for a feature.
    
    Args:
        feature_key: Feature key
        
    Returns:
        str: Icon emoji
    """
    return FEATURE_ICONS.get(feature_key, "🤖")

