"""
AI Feature Dispatcher

Central dispatcher for all AI feature execution.
Validates features by code, checks enable state, and routes to appropriate services.
"""
from flask import current_app
from typing import Dict, Any


def run_ai_feature(feature_code: str, payload: Dict[str, Any], user) -> Dict[str, Any]:
    """
    Execute an AI feature service.
    
    Args:
        feature_code: The feature code (e.g. 'ai_chat', 'event_planning')
        payload: Request payload dictionary
        user: Current user object
    
    Returns:
        dict: JSON-safe response with 'success' and 'data' or 'error' keys
    """
    try:
        from sas_management.ai.feature_registry import AI_FEATURES
        from sas_management.ai.models import AIFeature, is_feature_enabled
        
        # Validate feature_code exists in registry
        if feature_code not in AI_FEATURES:
            return {
                'success': False,
                'error': 'Feature not registered',
                'message': f'Feature "{feature_code}" is not registered in the system.'
            }
        
        # Query feature by code
        feature = AIFeature.query.filter_by(code=feature_code).first()
        if not feature:
            return {
                'success': False,
                'error': 'Feature not found',
                'message': f'Feature "{feature_code}" not found in database.'
            }
        
        # Check if feature is enabled
        if not is_feature_enabled(feature_code):
            return {
                'success': False,
                'error': 'Feature is disabled',
                'message': 'This AI feature is currently disabled. Please enable it to use it.'
            }
        
        # Import handler explicitly via if/elif map
        handler_module = _get_handler_module(feature_code)
        if not handler_module:
            return {
                'success': False,
                'error': 'Handler not available',
                'message': f'Handler for feature "{feature_code}" is not available.'
            }
        
        # Execute handler.run()
        try:
            result = handler_module.run(payload, user)
            
            # Ensure result has success field
            if not isinstance(result, dict):
                return {
                    'success': False,
                    'error': 'Invalid service response',
                    'message': 'The AI service returned an invalid response.'
                }
            
            if 'success' not in result:
                result['success'] = True
            
            return result
            
        except Exception as e:
            current_app.logger.exception(f"Error executing handler for '{feature_code}': {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An error occurred while processing your request.'
            }
        
    except Exception as e:
        current_app.logger.exception(f"Error in run_ai_feature for '{feature_code}': {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'An unexpected error occurred. Please try again.'
        }


def _get_handler_module(feature_code: str):
    """
    Get handler module by feature_code using explicit if/elif mapping.
    NO dynamic imports, NO string-based lookups.
    """
    if feature_code == 'ai_chat':
        try:
            from sas_management.ai.services import sas_chat
            return sas_chat
        except ImportError:
            return None
    elif feature_code == 'event_planning':
        try:
            from sas_management.ai.services import event_planning
            return event_planning
        except ImportError:
            return None
    elif feature_code == 'sales_forecasting':
        try:
            from sas_management.ai.services import sales_forecasting
            return sales_forecasting
        except ImportError:
            return None
    elif feature_code == 'staff_performance':
        try:
            from sas_management.ai.services import staff_performance
            return staff_performance
        except ImportError:
            return None
    elif feature_code == 'pricing_ai':
        try:
            from sas_management.ai.services import pricing_ai
            return pricing_ai
        except ImportError:
            return None
    elif feature_code == 'inventory_predictor':
        try:
            from sas_management.ai.services import inventory_predictor
            return inventory_predictor
        except ImportError:
            return None
    elif feature_code == 'risk_detection':
        try:
            from sas_management.ai.services import risk_detection
            return risk_detection
        except ImportError:
            return None
    elif feature_code == 'operations_chat':
        try:
            from sas_management.ai.services import operations_chat
            return operations_chat
        except ImportError:
            return None
    else:
        return None

