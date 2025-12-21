"""
AI Feature Registry Model - Safe and Isolated

This module provides the AIFeature model for managing AI feature enable/disable state.
The model is intentionally isolated with no foreign keys to prevent impact on existing tables.
"""
from flask import current_app
from sas_management.models import db


class AIFeature(db.Model):
    """
    AI Feature registry model for managing feature toggles.
    
    This model is safe and isolated:
    - No foreign keys
    - No impact on existing tables
    - Simple enable/disable state management
    
    Note: `code` is the ONLY identifier (NOT NULL, unique)
    """
    __tablename__ = "ai_features"
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)  # Single canonical identifier
    name = db.Column(db.String(255), nullable=False)  # Display name
    description = db.Column(db.Text, nullable=True)  # Feature description
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)  # Enable/disable toggle
    
    def __repr__(self):
        return f"<AIFeature {self.code} enabled={self.is_enabled}>"
    
    def to_dict(self):
        """Convert to dictionary for JSON responses."""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'is_enabled': self.is_enabled
        }


def is_feature_enabled(feature_code: str) -> bool:
    """
    Check if an AI feature is enabled.
    
    Args:
        feature_code: The feature code (canonical identifier, e.g. 'ai_chat', 'event_planning')
    
    Returns:
        bool: True if feature exists and is enabled, False otherwise.
              Returns False on any error (fail-safe).
    """
    try:
        # Query by code (canonical identifier)
        feature = AIFeature.query.filter_by(code=feature_code).first()
        if feature:
            return bool(feature.is_enabled)
        return False
    except Exception as e:
        # Fail-safe: return False on any error
        if current_app:
            current_app.logger.warning(f"Error checking feature '{feature_code}': {e}")
        return False


def ensure_default_ai_features():
    """
    Auto-seed AI features on app start.
    
    Hard reset: Only creates features that don't exist by code.
    Uses code as single source of identity.
    """
    from sas_management.ai.feature_registry import AI_FEATURES
    
    created_count = 0
    
    try:
        # Rollback any pending transactions
        db.session.rollback()
        
        # Use no_autoflush to prevent premature commits
        with db.session.no_autoflush:
            # Process each feature code from registry
            for feature_code, feature_name in AI_FEATURES.items():
                try:
                    # Check if feature already exists by code
                    existing = AIFeature.query.filter_by(code=feature_code).first()
                    
                    if not existing:
                        # Create new feature with code only
                        new_feature = AIFeature(
                            code=feature_code,
                            name=feature_name,
                            description='',
                            is_enabled=True
                        )
                        db.session.add(new_feature)
                        created_count += 1
                
                except Exception as e:
                    # Skip this feature if there's an error
                    if current_app:
                        current_app.logger.warning(f"Error checking/creating feature '{feature_code}': {e}")
                    continue
        
        # Commit ONCE at end
        if created_count > 0:
            db.session.commit()
            if current_app:
                current_app.logger.info(f"Auto-seeded {created_count} AI features")
            print(f"[AI] Auto-seeded {created_count} AI features")
        else:
            if current_app:
                current_app.logger.debug("All AI features already exist in database")
    
    except Exception as e:
        # Fail-safe: rollback and log, but don't crash the app
        db.session.rollback()
        error_msg = f"Error auto-seeding AI features: {e}"
        if current_app:
            current_app.logger.exception(error_msg)
        print(f"[WARNING] {error_msg}")

