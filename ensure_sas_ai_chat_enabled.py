"""
Script to ensure SAS AI Chat feature is enabled in the database.
Run this script to initialize or enable the sas_ai_chat feature.
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app creation - handle both direct import and module import
try:
    from sas_management.app import create_app
except ImportError:
    # Fallback: create app directly
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sas_management.app import create_app
from sas_management.models import db
from sas_management.ai.feature_model import AIFeature, ensure_default_ai_features

def ensure_sas_ai_chat_enabled():
    """Ensure sas_ai_chat feature exists and is enabled."""
    app = create_app()
    
    with app.app_context():
        try:
            # Ensure all default AI features exist
            ensure_default_ai_features()
            
            # Specifically ensure sas_ai_chat is enabled
            feature = AIFeature.query.filter_by(code="sas_ai_chat").first()
            
            if not feature:
                feature = AIFeature(
                    code="sas_ai_chat",
                    name="SAS AI Chat",
                    is_enabled=True
                )
                db.session.add(feature)
                print("[OK] Created sas_ai_chat feature")
            else:
                if not feature.is_enabled:
                    feature.is_enabled = True
                    print("[OK] Enabled sas_ai_chat feature")
                else:
                    print("[OK] sas_ai_chat feature is already enabled")
            
            db.session.commit()
            print("\n[OK] SAS AI Chat feature is now enabled and ready to use!")
            
            # Also ensure AI module config is set
            if not app.config.get("AI_MODULE_ENABLED", False):
                app.config["AI_MODULE_ENABLED"] = True
                print("[OK] AI module enabled in config")
            
            if not app.config.get("SAS_AI_ENABLED", False):
                app.config["SAS_AI_ENABLED"] = True
                print("[OK] SAS_AI_ENABLED set in config")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error ensuring SAS AI Chat is enabled: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("Ensuring SAS AI Chat feature is enabled...")
    success = ensure_sas_ai_chat_enabled()
    sys.exit(0 if success else 1)

