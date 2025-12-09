"""Unit tests for Production Department module."""
import json
from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app
from models import (
    Event,
    Ingredient,
    ProductionLineItem,
    ProductionOrder,
    Recipe,
    User,
    UserRole,
    db,
)


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False
    
    with app.app_context():
        db.create_all()
        # Create test user
        admin_user = User(email="test@test.com", role=UserRole.Admin)
        admin_user.set_password("password")
        db.session.add(admin_user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    # Login to get session
    client.post("/", data={"email": "test@test.com", "password": "password"})
    return {}


@pytest.fixture
def test_ingredient(app):
    """Create a test ingredient."""
    with app.app_context():
        ingredient = Ingredient(
            name="Test Chicken",
            unit_of_measure="kg",
            stock_count=Decimal("10.0"),
            unit_cost_ugx=Decimal("5000.00"),
        )
        db.session.add(ingredient)
        db.session.commit()
        return ingredient


@pytest.fixture
def test_recipe(app, test_ingredient):
    """Create a test recipe."""
    with app.app_context():
        ingredients_data = [
            {
                "ingredient_id": test_ingredient.id,
                "qty_per_portion": 0.2,
                "unit": "kg",
                "unit_cost": 5000.00,
            }
        ]
        recipe = Recipe(
            name="Chicken Curry",
            description="Test recipe",
            portions=10,
            ingredients=json.dumps(ingredients_data),
            prep_time_mins=30,
            cook_time_mins=60,
            cost_per_portion=Decimal("1000.00"),
        )
        db.session.add(recipe)
        db.session.commit()
        return recipe


@pytest.fixture
def test_event(app):
    """Create a test event."""
    with app.app_context():
        from models import Client
        
        client = Client(
            name="Test Client",
            contact_person="Test Person",
            phone="1234567890",
            email="client@test.com",
        )
        db.session.add(client)
        db.session.flush()
        
        event = Event(
            client_id=client.id,
            event_name="Test Event",
            event_date=datetime.now().date(),
            guest_count=50,
            status="Confirmed",
            quoted_value=Decimal("100000.00"),
        )
        db.session.add(event)
        db.session.commit()
        return event


def test_create_recipe(app, test_ingredient):
    """Test recipe creation."""
    with app.app_context():
        ingredients_data = [
            {
                "ingredient_id": test_ingredient.id,
                "qty_per_portion": 0.15,
                "unit": "kg",
            }
        ]
        recipe = Recipe(
            name="Test Recipe",
            portions=20,
            ingredients=json.dumps(ingredients_data),
            prep_time_mins=20,
            cook_time_mins=40,
        )
        db.session.add(recipe)
        db.session.commit()
        
        assert recipe.id is not None
        assert recipe.name == "Test Recipe"
        assert recipe.portions == 20


def test_create_production_order(app, test_recipe, test_event):
    """Test production order creation."""
    with app.app_context():
        from services.production_service import create_production_order
        
        items = [
            {
                "recipe_id": test_recipe.id,
                "portions": 50,
                "recipe_name": test_recipe.name,
            }
        ]
        schedule_times = {
            "prep": datetime.now().isoformat(),
            "cook": (datetime.now().replace(hour=10)).isoformat(),
        }
        
        order = create_production_order(test_event.id, items, schedule_times)
        
        assert order.id is not None
        assert order.reference.startswith("PROD-")
        assert order.event_id == test_event.id
        assert len(order.items) == 1
        assert order.items[0].portions == 50


def test_scale_recipe(app, test_recipe, test_ingredient):
    """Test recipe scaling."""
    with app.app_context():
        from services.production_service import scale_recipe
        
        scaled = scale_recipe(test_recipe.id, 50)  # Scale to 50 portions
        
        assert len(scaled) > 0
        # Base recipe is 10 portions, so 50 portions = 5x scale
        # 0.2 kg per portion * 5 = 1.0 kg
        # scaled returns dict with ingredient_id as key
        assert test_ingredient.id in scaled
        assert scaled[test_ingredient.id] == pytest.approx(1.0, rel=0.1)


def test_reserve_ingredients(app, test_ingredient):
    """Test ingredient reservation."""
    with app.app_context():
        from services.production_service import reserve_ingredients
        
        initial_stock = test_ingredient.stock_count
        ingredients_map = {test_ingredient.id: 2.0}
        
        reserved = reserve_ingredients(ingredients_map)
        
        db.session.refresh(test_ingredient)
        assert test_ingredient.stock_count == initial_stock - Decimal("2.0")
        assert len(reserved) == 1
        assert reserved[0]["ingredient_id"] == test_ingredient.id


def test_reserve_insufficient_stock(app, test_ingredient):
    """Test reservation with insufficient stock."""
    with app.app_context():
        from services.production_service import reserve_ingredients
        
        ingredients_map = {test_ingredient.id: 1000.0}  # More than available
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            reserve_ingredients(ingredients_map)


def test_api_create_order(client, auth_headers, test_recipe, test_event):
    """Test API endpoint for creating production order."""
    # Login first
    client.post("/", data={"email": "test@test.com", "password": "password"})
    
    data = {
        "event_id": test_event.id,
        "items": [
            {
                "recipe_id": test_recipe.id,
                "portions": 30,
                "recipe_name": test_recipe.name,
            }
        ],
        "schedule_times": {
            "prep": datetime.now().isoformat(),
        },
    }
    
    response = client.post(
        "/production/api/orders",
        json=data,
        headers={"Content-Type": "application/json"},
    )
    
    assert response.status_code == 201
    result = json.loads(response.data)
    assert result["status"] == "success"
    assert "order_id" in result
    assert "reference" in result


def test_api_list_orders(client, auth_headers, app, test_recipe, test_event):
    """Test API endpoint for listing orders."""
    # Login first
    client.post("/", data={"email": "test@test.com", "password": "password"})
    
    # Create an order first
    with app.app_context():
        from services.production_service import create_production_order
        
        items = [{"recipe_id": test_recipe.id, "portions": 20, "recipe_name": test_recipe.name}]
        schedule_times = {"prep": datetime.now().isoformat()}
        create_production_order(test_event.id, items, schedule_times)
    
    response = client.get("/production/api/orders")
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["status"] == "success"
    assert "orders" in result
    assert len(result["orders"]) > 0


def test_api_reserve_ingredients(client, auth_headers, app, test_recipe, test_ingredient, test_event):
    """Test API endpoint for reserving ingredients."""
    # Login first
    client.post("/", data={"email": "test@test.com", "password": "password"})
    
    # Create an order first
    with app.app_context():
        from services.production_service import create_production_order
        
        items = [{"recipe_id": test_recipe.id, "portions": 10, "recipe_name": test_recipe.name}]
        schedule_times = {"prep": datetime.now().isoformat()}
        order = create_production_order(test_event.id, items, schedule_times)
        order_id = order.id
    
    response = client.post(f"/production/api/orders/{order_id}/reserve")
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["status"] == "success"
    
    # Verify stock was decremented
    with app.app_context():
        db.session.refresh(test_ingredient)
        assert test_ingredient.stock_count < Decimal("10.0")


def test_api_update_status(client, auth_headers, app, test_recipe, test_event):
    """Test API endpoint for updating order status."""
    # Login first
    client.post("/", data={"email": "test@test.com", "password": "password"})
    
    # Create an order first
    with app.app_context():
        from services.production_service import create_production_order
        
        items = [{"recipe_id": test_recipe.id, "portions": 20, "recipe_name": test_recipe.name}]
        schedule_times = {"prep": datetime.now().isoformat()}
        order = create_production_order(test_event.id, items, schedule_times)
        order_id = order.id
    
    response = client.patch(
        f"/production/api/orders/{order_id}/status",
        json={"status": "In Prep"},
        headers={"Content-Type": "application/json"},
    )
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["status"] == "success"
    assert result["new_status"] == "In Prep"
    
    # Verify status was updated
    with app.app_context():
        order = ProductionOrder.query.get(order_id)
        assert order.status == "In Prep"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

