"""
SAS AI - Premium AI Features Hub

Central hub for all AI-powered features in the SAS Management System.
All features are assistive only - no autonomous writes.
"""
from .registry import get_feature_registry, is_feature_enabled
from .guards import ai_feature_required, require_ai_module
from .branding import get_value_color, get_feature_icon

__all__ = [
    'get_feature_registry',
    'is_feature_enabled',
    'ai_feature_required',
    'require_ai_module',
    'get_value_color',
    'get_feature_icon',
]

