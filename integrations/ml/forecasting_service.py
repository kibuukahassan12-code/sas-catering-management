"""ML forecasting service for sales and demand prediction."""
import os
from typing import Dict, List, Optional, Tuple
from flask import current_app

try:
    import pandas as pd
    import numpy as np
    from sklearn.linear_model import LinearRegression
    PANDAS_AVAILABLE = True
    SKLEARN_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    SKLEARN_AVAILABLE = False
    pd = None
    np = None
    LinearRegression = None

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None


class ForecastingService:
    """ML forecasting service for sales and demand prediction."""
    
    def __init__(self):
        self.mock_mode = os.getenv('INTEGRATIONS_MOCK', 'false').lower() == 'true'
        self.enabled = (PANDAS_AVAILABLE and SKLEARN_AVAILABLE) and not self.mock_mode
        
        if not self.enabled and current_app:
            current_app.logger.warning(
                "Forecasting service disabled. Using mock mode." if self.mock_mode else ""
            )
    
    def predict_sales(
        self,
        historical_data: List[Tuple[str, float]],  # [(date, value), ...]
        horizon: int = 30,
        model: str = 'simple'  # 'simple' or 'prophet'
    ) -> Dict[str, any]:
        """
        Predict future sales using historical data.
        
        Args:
            historical_data: List of (date, value) tuples
            horizon: Number of days to forecast
            model: 'simple' (linear regression) or 'prophet' (Facebook Prophet)
            
        Returns:
            Dict with 'success', 'forecast' (list of predictions), 'error'
        """
        if self.mock_mode or not self.enabled:
            # Mock forecast: simple trend continuation
            last_value = historical_data[-1][1] if historical_data else 1000
            forecast = [
                {
                    'date': f'2025-12-{i+1:02d}',
                    'predicted': last_value * (1 + 0.02 * i),  # 2% growth per day
                    'lower_bound': last_value * (1 + 0.01 * i),
                    'upper_bound': last_value * (1 + 0.03 * i)
                }
                for i in range(horizon)
            ]
            return {
                'success': True,
                'forecast': forecast,
                'model': 'mock',
                'mock': True
            }
        
        try:
            if model == 'prophet' and PROPHET_AVAILABLE:
                return self._prophet_forecast(historical_data, horizon)
            else:
                return self._simple_forecast(historical_data, horizon)
        except Exception as e:
            if current_app:
                current_app.logger.exception(f"Forecasting error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _simple_forecast(
        self,
        historical_data: List[Tuple[str, float]],
        horizon: int
    ) -> Dict[str, any]:
        """Simple linear regression forecast."""
        try:
            df = pd.DataFrame(historical_data, columns=['date', 'value'])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            df['days'] = (df['date'] - df['date'].min()).dt.days
            
            X = df[['days']].values
            y = df['value'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict future
            last_day = df['days'].max()
            future_days = np.arange(last_day + 1, last_day + 1 + horizon)
            predictions = model.predict(future_days.reshape(-1, 1))
            
            # Generate forecast dates
            last_date = df['date'].max()
            forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon)
            
            forecast = [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'predicted': float(pred),
                    'lower_bound': float(pred * 0.9),
                    'upper_bound': float(pred * 1.1)
                }
                for date, pred in zip(forecast_dates, predictions)
            ]
            
            return {
                'success': True,
                'forecast': forecast,
                'model': 'linear_regression',
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _prophet_forecast(
        self,
        historical_data: List[Tuple[str, float]],
        horizon: int
    ) -> Dict[str, any]:
        """Facebook Prophet forecast."""
        try:
            df = pd.DataFrame(historical_data, columns=['ds', 'y'])
            df['ds'] = pd.to_datetime(df['ds'])
            df = df.sort_values('ds')
            
            model = Prophet()
            model.fit(df)
            
            future = model.make_future_dataframe(periods=horizon)
            forecast = model.predict(future)
            
            # Get only future predictions
            future_forecast = forecast.tail(horizon)
            
            result = [
                {
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'predicted': float(row['yhat']),
                    'lower_bound': float(row['yhat_lower']),
                    'upper_bound': float(row['yhat_upper'])
                }
                for _, row in future_forecast.iterrows()
            ]
            
            return {
                'success': True,
                'forecast': result,
                'model': 'prophet',
                'mock': False
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def predict_demand(
        self,
        item_id: int,
        historical_sales: List[Tuple[str, int]],
        horizon: int = 7
    ) -> Dict[str, any]:
        """
        Predict demand for a specific item.
        
        Args:
            item_id: Item ID
            historical_sales: List of (date, quantity) tuples
            horizon: Days to forecast
            
        Returns:
            Dict with 'success', 'forecast', 'error'
        """
        # Convert to sales format and use predict_sales
        sales_data = [(date, float(qty)) for date, qty in historical_sales]
        result = self.predict_sales(sales_data, horizon, model='simple')
        
        if result['success']:
            # Convert back to integer quantities
            result['forecast'] = [
                {
                    **pred,
                    'predicted': int(pred['predicted']),
                    'lower_bound': int(pred['lower_bound']),
                    'upper_bound': int(pred['upper_bound'])
                }
                for pred in result['forecast']
            ]
        
        return result

