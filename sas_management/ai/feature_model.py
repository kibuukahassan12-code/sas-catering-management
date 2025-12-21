"""
Database-backed AI Feature model and helpers.

This module provides the canonical source of truth for AI feature
enable/disable state, as required by the SAS AI specifications.
"""
from typing import Optional

from flask import current_app

from sas_management.models import db


class AIFeature(db.Model):
    """
    Canonical AI feature definition.

    NOTE:
    - This model is intentionally minimal and focused on enable/disable state.
    - Metadata such as display name and descriptions still come from
      sas_management.ai.registry.FEATURE_DEFINITIONS.
    """
    __tablename__ = "ai_features"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)  # e.g. "event_planning_assistant"
    name = db.Column(db.String(255), nullable=False)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self) -> str:  # pragma: no cover - repr only
        return f"<AIFeature {self.code} enabled={self.is_enabled}>"


def is_ai_feature_enabled(feature_code: str) -> bool:
    """
    Check if an AI feature is enabled using the database-backed model.

    Args:
        feature_code: Stable string code, e.g. "event_planning_assistant"

    Returns:
        bool: True if feature exists and is_enabled is True, False otherwise.
    """
    if not feature_code:
        return False

    try:
        feature: Optional[AIFeature] = AIFeature.query.filter_by(code=feature_code).first()
        if not feature:
            current_app.logger.warning(f"is_ai_feature_enabled: feature with code '{feature_code}' not found")
            return False
        return bool(feature.is_enabled)
    except Exception as e:
        # Fail-safe: never break callers, just log and return False
        current_app.logger.exception(f"is_ai_feature_enabled error for code='{feature_code}': {e}")
        return False


def ensure_default_ai_features():
    """
    Ensure that all required AI features exist in the database.

    This should be called at application startup (e.g. from app factory)
    to keep the ai_features table in sync with expected feature set.
    """
    required = {
        "event_planning_assistant": "Event Planning Assistant",
        "inventory_predictor": "Inventory Predictor",
        "operations_chat_assistant": "Operations Chat Assistant",
        "sas_ai_chat": "SAS AI Chat",
        "sales_forecasting_ai": "Sales Forecasting AI",
        "staff_performance_ai": "Staff Performance AI",
        "pricing_recommendation_ai": "Pricing Recommendation AI",
        "risk_detection_ai": "Risk Detection AI",
    }

    created_any = False

    for code, name in required.items():
        try:
            feature: Optional[AIFeature] = AIFeature.query.filter_by(code=code).first()
            if not feature:
                feature = AIFeature(code=code, name=name, is_enabled=True)
                db.session.add(feature)
                created_any = True
        except Exception as e:
            current_app.logger.exception(f"Failed ensuring AI feature '{code}': {e}")
            db.session.rollback()

    if created_any:
        try:
            db.session.commit()
            current_app.logger.info("Default AI features ensured in ai_features table")
        except Exception as e:
            current_app.logger.exception(f"Failed committing default AI features: {e}")
            db.session.rollback()


