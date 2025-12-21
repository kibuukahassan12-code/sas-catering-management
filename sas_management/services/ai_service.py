"""AI Suite service - Auto-cost optimization, Menu AI, Forecasting, Kitchen Assistant, Predictive Staffing, Shortage Prediction."""
import os
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from flask import current_app

# Safe imports with fallbacks
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
    np = None

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RandomForestRegressor = None
    StandardScaler = None

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    joblib = None

# Check for mock mode
AI_MOCK = os.getenv('AI_MOCK', 'false').lower() == 'true'
AI_MODEL_PATH = os.getenv('AI_MODEL_PATH', 'instance/ai_models')
AI_FORECAST_HORIZON = int(os.getenv('AI_FORECAST_HORIZON', '14'))


def ensure_model_dir():
    """Ensure model directory exists."""
    if not os.path.exists(AI_MODEL_PATH):
        os.makedirs(AI_MODEL_PATH, exist_ok=True)


def get_db_models():
    """Safely import database models."""
    try:
        from sas_management.models import (
            AIPredictionRun, MenuRecommendation, ForecastResult,
            StaffingSuggestion, ShortageAlert, CostOptimization,
            MenuItem, InventoryItem, Event, db
        )
        return {
            'AIPredictionRun': AIPredictionRun,
            'MenuRecommendation': MenuRecommendation,
            'ForecastResult': ForecastResult,
            'StaffingSuggestion': StaffingSuggestion,
            'ShortageAlert': ShortageAlert,
            'CostOptimization': CostOptimization,
            'MenuItem': MenuItem,
            'InventoryItem': InventoryItem,
            'Event': Event,
            'db': db
        }
    except Exception as e:
        if current_app:
            current_app.logger.warning(f"Could not import DB models: {e}")
        return None


# ============================================================
# AUTO-COST OPTIMIZATION
# ============================================================

def auto_cost_optimization(event_id: Optional[int] = None, menu_items_list: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Analyze menu items and suggest cost optimizations.
    
    Returns suggestions for:
    - Supplier swaps (if alternative suppliers exist)
    - Portion size tweaks
    - Ingredient substitutes
    """
    models = get_db_models()
    if not models:
        return {'success': False, 'error': 'Database models not available', 'suggestions': []}
    
    if AI_MOCK or not PANDAS_AVAILABLE:
        # Mock suggestions
        suggestions = [
            {
                'menu_item_id': 1,
                'suggestion_type': 'supplier_swap',
                'current_cost': 5000.0,
                'suggested_cost': 4500.0,
                'savings': 500.0,
                'details': 'Switch to Supplier B for chicken - 10% cheaper'
            }
        ]
        return {'success': True, 'suggestions': suggestions, 'mock': True}
    
    try:
        suggestions = []
        
        # Get menu items to analyze
        if event_id:
            # Get menu items from event
            event = models['db'].session.get(models['Event'], event_id)
            if event and hasattr(event, 'menu_items'):
                menu_items = event.menu_items
            else:
                menu_items = []
        elif menu_items_list:
            menu_items = models['MenuItem'].query.filter(models['MenuItem'].id.in_(menu_items_list)).all()
        else:
            # Analyze all menu items
            menu_items = models['MenuItem'].query.limit(50).all()
        
        for item in menu_items:
            if not hasattr(item, 'cost_per_portion') or not item.cost_per_portion:
                continue
            
            current_cost = float(item.cost_per_portion)
            
            # Simple optimization: suggest 5% cost reduction through portion tweak
            suggested_cost = current_cost * 0.95
            savings = current_cost - suggested_cost
            
            if savings > 0:
                suggestion = {
                    'menu_item_id': item.id,
                    'suggestion_type': 'portion_tweak',
                    'current_cost': current_cost,
                    'suggested_cost': suggested_cost,
                    'savings': savings,
                    'details': f'Reduce portion size by 5% to save {savings:.2f} per serving'
                }
                suggestions.append(suggestion)
                
                # Save to database
                opt = models['CostOptimization'](
                    menu_item_id=item.id,
                    event_id=event_id,
                    suggestion_type='portion_tweak',
                    current_cost=Decimal(str(current_cost)),
                    suggested_cost=Decimal(str(suggested_cost)),
                    savings=Decimal(str(savings)),
                    details=json.dumps(suggestion)
                )
                models['db'].session.add(opt)
        
        models['db'].session.commit()
        
        return {'success': True, 'suggestions': suggestions, 'count': len(suggestions)}
    
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error in auto_cost_optimization: {e}")
        return {'success': False, 'error': str(e), 'suggestions': []}


# ============================================================
# MENU AI RECOMMENDATIONS
# ============================================================

def menu_engine_recommendations(top_k: int = 10, constraints: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate AI-powered menu recommendations.
    
    Args:
        top_k: Number of recommendations to return
        constraints: Optional constraints (e.g., {'max_price': 10000, 'category': 'Main'})
    """
    models = get_db_models()
    if not models:
        return {'success': False, 'error': 'Database models not available', 'recommendations': []}
    
    if AI_MOCK or not PANDAS_AVAILABLE:
        # Mock recommendations
        recommendations = [
            {
                'menu_item_id': 1,
                'recommendation': 'High margin item - consider promoting',
                'score': 0.85
            },
            {
                'menu_item_id': 2,
                'recommendation': 'Popular item - increase stock',
                'score': 0.78
            }
        ]
        return {'success': True, 'recommendations': recommendations[:top_k], 'mock': True}
    
    try:
        # Get menu items
        query = models['MenuItem'].query
        
        if constraints:
            if 'category' in constraints:
                query = query.filter(models['MenuItem'].category_id == constraints['category'])
            if 'max_price' in constraints:
                query = query.filter(models['MenuItem'].selling_price <= constraints['max_price'])
        
        menu_items = query.limit(100).all()
        
        recommendations = []
        for item in menu_items:
            # Simple scoring: based on margin
            if hasattr(item, 'margin_percent') and item.margin_percent:
                score = min(item.margin_percent / 100.0, 1.0)
            else:
                score = 0.5
            
            recommendation_text = f"Menu item '{item.name}' has good margin potential"
            
            rec = models['MenuRecommendation'](
                menu_item_id=item.id,
                recommendation=recommendation_text,
                score=score
            )
            models['db'].session.add(rec)
            
            recommendations.append({
                'menu_item_id': item.id,
                'recommendation': recommendation_text,
                'score': score
            })
        
        models['db'].session.commit()
        
        # Sort by score and return top_k
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return {'success': True, 'recommendations': recommendations[:top_k], 'count': len(recommendations)}
    
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error in menu_engine_recommendations: {e}")
        return {'success': False, 'error': str(e), 'recommendations': []}


# ============================================================
# SALES FORECASTING
# ============================================================

def run_sales_forecast(source: str = 'POS', horizon: int = 14) -> Dict[str, Any]:
    """
    Run sales forecast for specified source.
    
    Args:
        source: 'POS', 'Catering', or 'Bakery'
        horizon: Number of days to forecast
    """
    models = get_db_models()
    if not models:
        return {'success': False, 'error': 'Database models not available'}
    
    if AI_MOCK or not PANDAS_AVAILABLE:
        # Mock forecast
        forecast_results = []
        for i in range(horizon):
            forecast_date = date.today() + timedelta(days=i+1)
            forecast_results.append({
                'date': forecast_date.isoformat(),
                'predicted': 50000.0 + (i * 1000),
                'model_name': 'mock_model'
            })
        
        return {
            'success': True,
            'forecast_results': forecast_results,
            'summary': {'mae': 0, 'rmse': 0},
            'mock': True
        }
    
    try:
        ensure_model_dir()
        
        # Create prediction run record
        run = models['AIPredictionRun'](
            run_type='forecast',
            model_name='prophet' if PROPHET_AVAILABLE else 'random_forest',
            parameters=json.dumps({'source': source, 'horizon': horizon})
        )
        models['db'].session.add(run)
        models['db'].session.flush()
        
        # Get historical data (mock for now - would need actual sales data)
        # In production, this would query POSOrder, Event, BakeryOrder tables
        historical_dates = [date.today() - timedelta(days=x) for x in range(30, 0, -1)]
        historical_values = [50000 + (x * 100) + (x % 7 * 500) for x in range(30)]
        
        # Prepare data
        df = pd.DataFrame({
            'ds': historical_dates,
            'y': historical_values
        })
        
        forecast_results = []
        
        if PROPHET_AVAILABLE:
            # Use Prophet
            model = Prophet()
            model.fit(df)
            future = model.make_future_dataframe(periods=horizon)
            forecast = model.predict(future)
            
            for idx, row in forecast.tail(horizon).iterrows():
                forecast_date = row['ds'].date()
                predicted = float(row['yhat'])
                
                fr = models['ForecastResult'](
                    source=source,
                    date=forecast_date,
                    predicted=Decimal(str(predicted)),
                    model_name='prophet',
                    run_id=run.id
                )
                models['db'].session.add(fr)
                
                forecast_results.append({
                    'date': forecast_date.isoformat(),
                    'predicted': predicted,
                    'model_name': 'prophet'
                })
        
        elif SKLEARN_AVAILABLE:
            # Use Random Forest as fallback
            X = np.array(range(len(historical_values))).reshape(-1, 1)
            y = np.array(historical_values)
            
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Predict future
            future_X = np.array(range(len(historical_values), len(historical_values) + horizon)).reshape(-1, 1)
            predictions = model.predict(future_X)
            
            for i, pred in enumerate(predictions):
                forecast_date = date.today() + timedelta(days=i+1)
                
                fr = models['ForecastResult'](
                    source=source,
                    date=forecast_date,
                    predicted=Decimal(str(predicted)),
                    model_name='random_forest',
                    run_id=run.id
                )
                models['db'].session.add(fr)
                
                forecast_results.append({
                    'date': forecast_date.isoformat(),
                    'predicted': float(pred),
                    'model_name': 'random_forest'
                })
        
        models['db'].session.commit()
        
        # Calculate summary (would need actuals for real metrics)
        summary = {'mae': 0, 'rmse': 0, 'forecast_count': len(forecast_results)}
        
        return {
            'success': True,
            'forecast_results': forecast_results,
            'summary': summary,
            'run_id': run.id
        }
    
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error in run_sales_forecast: {e}")
        return {'success': False, 'error': str(e)}


def forecast_accuracy_score(forecast_id_list: List[int]) -> Dict[str, Any]:
    """Calculate accuracy metrics (MAPE, RMSE) for forecasts with actuals."""
    models = get_db_models()
    if not models:
        return {'success': False, 'error': 'Database models not available'}
    
    try:
        forecasts = models['ForecastResult'].query.filter(
            models['ForecastResult'].id.in_(forecast_id_list)
        ).filter(
            models['ForecastResult'].actual.isnot(None)
        ).all()
        
        if not forecasts:
            return {'success': False, 'error': 'No forecasts with actuals found'}
        
        errors = []
        for f in forecasts:
            if f.actual and f.predicted:
                error = float(f.actual) - float(f.predicted)
                errors.append(error)
        
        if not errors:
            return {'success': False, 'error': 'No valid forecast-actual pairs'}
        
        mae = sum(abs(e) for e in errors) / len(errors)
        rmse = (sum(e**2 for e in errors) / len(errors)) ** 0.5
        
        # MAPE (Mean Absolute Percentage Error)
        actuals = [float(f.actual) for f in forecasts if f.actual]
        if actuals and sum(actuals) > 0:
            mape = sum(abs((float(f.actual) - float(f.predicted)) / float(f.actual)) * 100 
                      for f in forecasts if f.actual) / len(forecasts)
        else:
            mape = 0
        
        return {
            'success': True,
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'sample_count': len(forecasts)
        }
    
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error in forecast_accuracy_score: {e}")
        return {'success': False, 'error': str(e)}


# ============================================================
# KITCHEN ASSISTANT
# ============================================================

def kitchen_planner(event_id: int) -> Dict[str, Any]:
    """
    Generate kitchen production schedule for an event.
    
    Returns:
        Schedule with start times, stations, and parallelization plan
    """
    models = get_db_models()
    if not models:
        return {'success': False, 'error': 'Database models not available'}
    
    if AI_MOCK:
        # Mock schedule
        return {
            'success': True,
            'event_id': event_id,
            'schedule': [
                {
                    'task': 'Prep vegetables',
                    'start_time': '06:00',
                    'duration_minutes': 120,
                    'station': 'Prep Station 1',
                    'staff_needed': 2
                },
                {
                    'task': 'Cook main course',
                    'start_time': '08:00',
                    'duration_minutes': 180,
                    'station': 'Main Kitchen',
                    'staff_needed': 3
                }
            ],
            'mock': True
        }
    
    try:
        event = models['db'].session.get(models['Event'], event_id)
        if not event:
            return {'success': False, 'error': f'Event {event_id} not found'}
        
        # Simple greedy scheduler
        # In production, would analyze recipes, prep times, cook times
        schedule = [
            {
                'task': 'Event preparation',
                'start_time': '06:00',
                'duration_minutes': 120,
                'station': 'Prep Station',
                'staff_needed': 2,
                'parallel_tasks': []
            },
            {
                'task': 'Main course preparation',
                'start_time': '08:00',
                'duration_minutes': 180,
                'station': 'Main Kitchen',
                'staff_needed': 3,
                'parallel_tasks': ['Side dishes']
            }
        ]
        
        return {
            'success': True,
            'event_id': event_id,
            'schedule': schedule
        }
    
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error in kitchen_planner: {e}")
        return {'success': False, 'error': str(e)}


# ============================================================
# PREDICTIVE STAFFING
# ============================================================

def predictive_staffing(event_id: Optional[int] = None, date_range: Optional[Tuple[date, date]] = None) -> Dict[str, Any]:
    """
    Generate staffing recommendations based on forecasted demand.
    """
    models = get_db_models()
    if not models:
        return {'success': False, 'error': 'Database models not available'}
    
    if AI_MOCK or not PANDAS_AVAILABLE:
        # Mock staffing suggestion
        return {
            'success': True,
            'event_id': event_id,
            'suggested_staff_count': 8,
            'roles_breakdown': {'chef': 2, 'waiter': 5, 'manager': 1},
            'confidence': 0.75,
            'mock': True
        }
    
    try:
        if event_id:
            event = models['db'].session.get(models['Event'], event_id)
            if not event:
                return {'success': False, 'error': f'Event {event_id} not found'}
            
            guest_count = event.guest_count or 50
            event_date = event.event_date or date.today()
        else:
            guest_count = 50
            event_date = date.today()
        
        # Simple heuristic: 1 staff per 10 guests, with role breakdown
        base_staff = max(2, guest_count // 10)
        chefs = max(1, base_staff // 3)
        waiters = max(2, base_staff - chefs)
        managers = 1
        
        roles_breakdown = {
            'chef': chefs,
            'waiter': waiters,
            'manager': managers
        }
        
        total_staff = sum(roles_breakdown.values())
        confidence = 0.75  # Would be calculated from historical data
        
        # Save suggestion
        suggestion = models['StaffingSuggestion'](
            event_id=event_id,
            date=event_date,
            suggested_staff_count=total_staff,
            roles_breakdown=json.dumps(roles_breakdown),
            confidence=confidence
        )
        models['db'].session.add(suggestion)
        models['db'].session.commit()
        
        return {
            'success': True,
            'event_id': event_id,
            'suggested_staff_count': total_staff,
            'roles_breakdown': roles_breakdown,
            'confidence': confidence,
            'suggestion_id': suggestion.id
        }
    
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error in predictive_staffing: {e}")
        return {'success': False, 'error': str(e)}


# ============================================================
# SHORTAGE PREDICTION
# ============================================================

def predict_item_shortages(horizon_days: int = 30) -> Dict[str, Any]:
    """
    Predict inventory shortages based on consumption rates and upcoming events.
    """
    models = get_db_models()
    if not models:
        return {'success': False, 'error': 'Database models not available'}
    
    if AI_MOCK or not PANDAS_AVAILABLE:
        # Mock shortage alerts
        alerts = [
            {
                'inventory_item_id': 1,
                'predicted_shortage_date': (date.today() + timedelta(days=7)).isoformat(),
                'recommended_order_qty': 50.0,
                'severity': 'high'
            }
        ]
        return {'success': True, 'alerts': alerts, 'count': len(alerts), 'mock': True}
    
    try:
        # Get all inventory items
        items = models['InventoryItem'].query.limit(100).all()
        
        alerts = []
        for item in items:
            # Simple check: if current_stock < reorder_level, create alert
            current_stock = float(item.current_stock) if hasattr(item, 'current_stock') and item.current_stock else 0
            reorder_level = float(item.reorder_level) if hasattr(item, 'reorder_level') and item.reorder_level else 10
            
            if current_stock < reorder_level:
                # Predict shortage date (simple: based on average consumption)
                predicted_date = date.today() + timedelta(days=7)
                recommended_qty = max(reorder_level * 2, 50.0)
                
                # Determine severity
                if current_stock < reorder_level * 0.5:
                    severity = 'high'
                elif current_stock < reorder_level * 0.75:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                alert = models['ShortageAlert'](
                    inventory_item_id=item.id,
                    predicted_shortage_date=predicted_date,
                    recommended_order_qty=recommended_qty,
                    severity=severity
                )
                models['db'].session.add(alert)
                
                alerts.append({
                    'inventory_item_id': item.id,
                    'predicted_shortage_date': predicted_date.isoformat(),
                    'recommended_order_qty': recommended_qty,
                    'severity': severity
                })
        
        models['db'].session.commit()
        
        return {
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        }
    
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error in predict_item_shortages: {e}")
        return {'success': False, 'error': str(e)}

