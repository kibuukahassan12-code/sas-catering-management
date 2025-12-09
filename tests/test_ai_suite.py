"""Tests for AI Suite."""
import pytest
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def app():
    """Create test app."""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        from models import db
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_menu_recommendation_returns_list(app):
    """Test that menu recommendations return a list."""
    with app.app_context():
        from services.ai_service import menu_engine_recommendations
        
        result = menu_engine_recommendations(top_k=5)
        
        assert result['success'] is True
        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)


def test_forecast_runs_and_saves(app):
    """Test that forecast runs and saves results."""
    with app.app_context():
        from services.ai_service import run_sales_forecast
        from models import ForecastResult, db
        
        result = run_sales_forecast(source='POS', horizon=7)
        
        assert result['success'] is True
        assert 'forecast_results' in result
        
        # Check that results were saved to DB
        saved = ForecastResult.query.filter_by(source='POS').all()
        assert len(saved) > 0 or result.get('mock', False)


def test_shortage_alert_generation(app):
    """Test that shortage alerts are generated."""
    with app.app_context():
        from services.ai_service import predict_item_shortages
        from models import ShortageAlert, InventoryItem, db
        
        # Create a test inventory item
        item = InventoryItem(
            name="Test Item",
            unit="kg",
            current_stock=5.0,
            reorder_level=10.0
        )
        db.session.add(item)
        db.session.commit()
        
        result = predict_item_shortages(horizon_days=30)
        
        assert result['success'] is True
        assert 'alerts' in result
        assert isinstance(result['alerts'], list)


def test_kitchen_planner_returns_schedule(app):
    """Test that kitchen planner returns a schedule."""
    with app.app_context():
        from services.ai_service import kitchen_planner
        from models import Event, Client, db
        
        # Create test event
        client = Client(name="Test Client", email="test@example.com", phone="1234567890")
        db.session.add(client)
        db.session.flush()
        
        event = Event(
            event_name="Test Event",
            client_id=client.id,
            event_date=date.today() + timedelta(days=7),
            guest_count=50
        )
        db.session.add(event)
        db.session.commit()
        
        result = kitchen_planner(event.id)
        
        assert result['success'] is True
        assert 'schedule' in result
        assert isinstance(result['schedule'], list)


def test_cost_optimization(app):
    """Test cost optimization function."""
    with app.app_context():
        from services.ai_service import auto_cost_optimization
        
        result = auto_cost_optimization()
        
        assert result['success'] is True
        assert 'suggestions' in result
        assert isinstance(result['suggestions'], list)


def test_predictive_staffing(app):
    """Test predictive staffing function."""
    with app.app_context():
        from services.ai_service import predictive_staffing
        from models import Event, Client, db
        
        # Create test event
        client = Client(name="Test Client", email="test@example.com", phone="1234567890")
        db.session.add(client)
        db.session.flush()
        
        event = Event(
            event_name="Test Event",
            client_id=client.id,
            event_date=date.today() + timedelta(days=7),
            guest_count=100
        )
        db.session.add(event)
        db.session.commit()
        
        result = predictive_staffing(event_id=event.id)
        
        assert result['success'] is True
        assert 'suggested_staff_count' in result
        assert result['suggested_staff_count'] > 0

