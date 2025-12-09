"""Food Safety service."""
from flask import current_app

def check_temperature_threshold(temp_c, item_type='general'):
    """Check if temperature is within safe range."""
    thresholds = {
        'hot_food': (60, 100),
        'cold_food': (-2, 5),
        'frozen': (-25, -15),
        'general': (0, 10)
    }
    
    min_temp, max_temp = thresholds.get(item_type, thresholds['general'])
    is_safe = min_temp <= float(temp_c) <= max_temp
    
    return {'success': True, 'is_safe': is_safe, 'min': min_temp, 'max': max_temp}

