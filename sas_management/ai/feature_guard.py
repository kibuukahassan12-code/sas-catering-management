import logging
from flask import current_app

logger = logging.getLogger(__name__)


def ai_features_state():
    """
    Single source of truth for SAS AI feature availability.
    Phase 2: observe + log only.
    """
    try:
        # Phase 2: static defaults – no enforcement, observation only.
        return {
            "ai_enabled": True,
            "voice_enabled": True,
            "system_queries_enabled": True,
        }
    except Exception as e:
        logger.warning("AI feature state error: %s", e)
        return {
            "ai_enabled": False,
            "voice_enabled": False,
            "system_queries_enabled": False,
        }


def log_if_disabled(feature_name, route_name):
    state = ai_features_state()
    if not state.get(feature_name, False):
        logger.warning(
            "AI feature '%s' disabled but route accessed: %s",
            feature_name,
            route_name,
        )


def ai_enabled():
    """
    Backwards-compatible helper used in Phase 1.
    Delegates to ai_features_state without enforcing access.
    """
    return bool(ai_features_state().get("ai_enabled", False))

