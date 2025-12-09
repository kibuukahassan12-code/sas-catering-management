"""ML integration services."""
try:
    from .forecasting_service import ForecastingService
except Exception:
    ForecastingService = None

__all__ = ['ForecastingService']
