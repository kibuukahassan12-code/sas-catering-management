"""
AI Feature State Management

Centralized runtime state management for AI features.
Enables/disables features dynamically without restart.
State is persisted in app.config only (no database).
"""
from flask import current_app
from typing import Dict, Optional


def _get_feature_state() -> Dict[str, bool]:
    """
    Get current feature state from app config.
    Initializes from config if not already set.
    
    Returns:
        Dictionary mapping feature keys to enabled status
    """
    state = current_app.config.get("AI_FEATURES", {})
    
    # If state is empty, initialize from config defaults
    if not state:
        from sas_management.ai.registry import FEATURE_DEFINITIONS
        # Initialize all features from config defaults (all enabled by default)
        state = {}
        for feature_key in FEATURE_DEFINITIONS.keys():
            # Check if there's a config value, otherwise default to True
            env_key = f"AI_FEATURE_{feature_key.upper()}"
            state[feature_key] = current_app.config.get(env_key, True)
        current_app.config["AI_FEATURES"] = state
    
    return state.copy()


def _set_feature_state(state: Dict[str, bool]):
    """
    Update feature state in app config.
    
    Args:
        state: Dictionary mapping feature keys to enabled status
    """
    current_app.config["AI_FEATURES"] = state.copy()


def is_enabled(feature_key: str) -> bool:
    """
    Check if a feature is enabled.
    
    Args:
        feature_key: Feature key to check
        
    Returns:
        True if feature is enabled, False otherwise
    """
    # First check if AI module is enabled (defaults to True from config)
    if not current_app.config.get("AI_MODULE_ENABLED", True):
        return False
    
    # Then check feature-specific flag (defaults to True if not set)
    state = _get_feature_state()
    # Default to True if not explicitly set to False
    return state.get(feature_key, True)


def enable(feature_key: str) -> bool:
    """
    Enable a feature at runtime.
    
    Args:
        feature_key: Feature key to enable
        
    Returns:
        True if enabled successfully, False if feature doesn't exist
    """
    from sas_management.ai.registry import FEATURE_DEFINITIONS
    
    # Validate feature exists
    if feature_key not in FEATURE_DEFINITIONS:
        return False
    
    state = _get_feature_state()
    state[feature_key] = True
    _set_feature_state(state)
    
    current_app.logger.info(f"AI feature '{feature_key}' enabled at runtime")
    return True


def disable(feature_key: str) -> bool:
    """
    Disable a feature at runtime.
    
    Args:
        feature_key: Feature key to disable
        
    Returns:
        True if disabled successfully, False if feature doesn't exist
    """
    from sas_management.ai.registry import FEATURE_DEFINITIONS
    
    # Validate feature exists
    if feature_key not in FEATURE_DEFINITIONS:
        return False
    
    state = _get_feature_state()
    state[feature_key] = False
    _set_feature_state(state)
    
    current_app.logger.info(f"AI feature '{feature_key}' disabled at runtime")
    return True


def get_all_features_state() -> Dict[str, bool]:
    """
    Get enabled state for all features.
    
    Returns:
        Dictionary mapping all feature keys to enabled status
    """
    from sas_management.ai.registry import FEATURE_DEFINITIONS
    
    state = _get_feature_state()
    result = {}
    
    for feature_key in FEATURE_DEFINITIONS.keys():
        result[feature_key] = state.get(feature_key, False)
    
    return result


def is_module_enabled() -> bool:
    """
    Check if AI module is enabled.
    
    Returns:
        True if module is enabled, False otherwise
    """
    return current_app.config.get("AI_MODULE_ENABLED", False)

