"""Seed comprehensive sample data for AI Suite testing."""
import os
import sys
import json
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app components directly
from flask import Flask
from config import Config
from models import (
    db, MenuItem, MenuCategory, Event, Client, InventoryItem, Ingredient,
    ForecastResult, AIPredictionRun, MenuRecommendation, CostOptimization,
    StaffingSuggestion, ShortageAlert
)


def seed_ai_data():
    """Seed comprehensive sample data for AI features."""
    # Create minimal Flask app for seeding
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("🌱 Seeding AI Suite sample data...")
        print("=" * 70)
        
        # ============================================================
        # 1. CREATE MENU CATEGORIES & MENU ITEMS
        # ============================================================
        print("\n📋 Creating menu items...")
        
        categories_data = [
            {"name": "Main Courses", "items": [
                {"name": "Grilled Chicken Breast", "cost": 4500, "price": 8500, "desc": "Tender grilled chicken with herbs"},
                {"name": "Beef Steak", "cost": 6000, "price": 12000, "desc": "Premium beef steak with sauce"},
                {"name": "Fish Fillet", "cost": 5000, "price": 9500, "desc": "Fresh fish fillet grilled to perfection"},
                {"name": "Vegetarian Pasta", "cost": 3000, "price": 7000, "desc": "Creamy pasta with vegetables"},
            ]},
            {"name": "Sides", "items": [
                {"name": "French Fries", "cost": 1500, "price": 4000, "desc": "Crispy golden fries"},
                {"name": "Vegetable Salad", "cost": 2000, "price": 5000, "desc": "Fresh mixed vegetables"},
                {"name": "Coleslaw", "cost": 1200, "price": 3500, "desc": "Creamy coleslaw"},
            ]},
            {"name": "Desserts", "items": [
                {"name": "Chocolate Cake", "cost": 2500, "price": 6000, "desc": "Rich chocolate cake slice"},
                {"name": "Fruit Salad", "cost": 1800, "price": 4500, "desc": "Fresh seasonal fruits"},
            ]},
        ]
        
        menu_items_created = 0
        for cat_data in categories_data:
            category = MenuCategory.query.filter_by(name=cat_data["name"]).first()
            if not category:
                category = MenuCategory(name=cat_data["name"])
                db.session.add(category)
                db.session.flush()
            
            for item_data in cat_data["items"]:
                existing = MenuItem.query.filter_by(name=item_data["name"]).first()
                if not existing:
                    margin = ((item_data["price"] - item_data["cost"]) / item_data["price"]) * 100
                    menu_item = MenuItem(
                        name=item_data["name"],
                        category_id=category.id,
                        description=item_data["desc"],
                        cost_per_portion=Decimal(str(item_data["cost"])),
                        selling_price=Decimal(str(item_data["price"])),
                        margin_percent=margin
                    )
                    db.session.add(menu_item)
                    menu_items_created += 1
        
        db.session.commit()
        print(f"   ✅ Created {menu_items_created} menu items")
        
        # ============================================================
        # 2. CREATE CLIENTS & EVENTS
        # ============================================================
        print("\n📅 Creating events...")
        
        clients_data = [
            {"name": "ABC Corporation", "email": "events@abc-corp.com", "phone": "+256 700 111 222", "contact_person": "John Doe"},
            {"name": "XYZ Events Ltd", "email": "contact@xyzevents.com", "phone": "+256 700 333 444", "contact_person": "Jane Smith"},
            {"name": "Grand Hotel", "email": "catering@grandhotel.com", "phone": "+256 700 555 666", "contact_person": "Robert Johnson"},
        ]
        
        clients = []
        for client_data in clients_data:
            client = Client.query.filter_by(email=client_data["email"]).first()
            if not client:
                client = Client(**client_data)
                db.session.add(client)
                db.session.flush()
            clients.append(client)
        
        # Create events with varied guest counts and dates
        events_data = [
            {"name": "Corporate Annual Dinner", "guest_count": 150, "days_ahead": 5, "type": "Corporate"},
            {"name": "Wedding Reception", "guest_count": 200, "days_ahead": 10, "type": "Wedding"},
            {"name": "Birthday Party", "guest_count": 50, "days_ahead": 3, "type": "Birthday"},
            {"name": "Conference Lunch", "guest_count": 80, "days_ahead": 7, "type": "Corporate"},
            {"name": "Anniversary Celebration", "guest_count": 120, "days_ahead": 14, "type": "Anniversary"},
            {"name": "Product Launch", "guest_count": 100, "days_ahead": 20, "type": "Corporate"},
            {"name": "Graduation Party", "guest_count": 75, "days_ahead": 12, "type": "Celebration"},
            {"name": "Gala Dinner", "guest_count": 300, "days_ahead": 25, "type": "Corporate"},
        ]
        
        events_created = 0
        for i, event_data in enumerate(events_data):
            event_date = date.today() + timedelta(days=event_data["days_ahead"])
            existing = Event.query.filter_by(
                event_name=event_data["name"],
                event_date=event_date
            ).first()
            
            if not existing:
                client = clients[i % len(clients)]
                quoted_value = event_data["guest_count"] * 15000  # ~15k per guest
                
                event = Event(
                    event_name=event_data["name"],
                    client_id=client.id,
                    event_date=event_date,
                    event_time="18:00",
                    guest_count=event_data["guest_count"],
                    event_type=event_data["type"],
                    status="Confirmed",
                    quoted_value=Decimal(str(quoted_value)),
                    venue=f"Venue {i+1}"
                )
                db.session.add(event)
                events_created += 1
        
        db.session.commit()
        print(f"   ✅ Created {events_created} events")
        
        # ============================================================
        # 3. CREATE INVENTORY ITEMS (Some with low stock for shortages)
        # ============================================================
        print("\n📦 Creating inventory items...")
        
        inventory_data = [
            # Items that will trigger shortage alerts (below reorder level)
            {"name": "Chicken Breast", "unit": "kg", "stock": 25.0, "reorder": 50.0},
            {"name": "Beef", "unit": "kg", "stock": 15.0, "reorder": 40.0},
            {"name": "Cooking Oil", "unit": "liters", "stock": 10.0, "reorder": 20.0},
            {"name": "Rice", "unit": "kg", "stock": 30.0, "reorder": 50.0},
            # Items with adequate stock
            {"name": "Mixed Vegetables", "unit": "kg", "stock": 100.0, "reorder": 25.0},
            {"name": "Flour", "unit": "kg", "stock": 80.0, "reorder": 30.0},
            {"name": "Sugar", "unit": "kg", "stock": 60.0, "reorder": 20.0},
            {"name": "Tomatoes", "unit": "kg", "stock": 45.0, "reorder": 15.0},
        ]
        
        inventory_created = 0
        for item_data in inventory_data:
            existing = InventoryItem.query.filter_by(name=item_data["name"]).first()
            if not existing:
                inventory_item = InventoryItem(
                    name=item_data["name"],
                    stock_count=int(item_data["stock"]),
                )
                db.session.add(inventory_item)
                inventory_created += 1
        
        db.session.commit()
        print(f"   ✅ Created {inventory_created} inventory items")
        
        # ============================================================
        # 4. CREATE FORECAST RESULTS (Historical + Future)
        # ============================================================
        print("\n📈 Creating forecast data...")
        
        sources = ['POS', 'Catering', 'Bakery']
        forecast_created = 0
        
        for source in sources:
            # Historical data (last 30 days) with actuals
            run_historical = AIPredictionRun(
                run_type='forecast',
                model_name='prophet',
                parameters=json.dumps({"source": source, "horizon": 30}),
                created_at=datetime.now(timezone.utc) - timedelta(days=35)
            )
            db.session.add(run_historical)
            db.session.flush()
            
            for i in range(30):
                forecast_date = date.today() - timedelta(days=30-i)
                base_value = {'POS': 50000, 'Catering': 200000, 'Bakery': 30000}[source]
                predicted = base_value + (i * 500) + ((i % 7) * 1000)
                # Add some variance to actuals
                actual = predicted + ((i % 5 - 2) * 1000)
                
                forecast = ForecastResult(
                    source=source,
                    date=forecast_date,
                    predicted=Decimal(str(predicted)),
                    actual=Decimal(str(actual)),
                    model_name='prophet',
                    run_id=run_historical.id
                )
                db.session.add(forecast)
                forecast_created += 1
            
            # Future forecasts (next 14 days)
            run_future = AIPredictionRun(
                run_type='forecast',
                model_name='prophet',
                parameters=json.dumps({"source": source, "horizon": 14}),
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(run_future)
            db.session.flush()
            
            for i in range(14):
                forecast_date = date.today() + timedelta(days=i+1)
                base_value = {'POS': 50000, 'Catering': 200000, 'Bakery': 30000}[source]
                predicted = base_value + ((30 + i) * 500) + (((30 + i) % 7) * 1000)
                
                forecast = ForecastResult(
                    source=source,
                    date=forecast_date,
                    predicted=Decimal(str(predicted)),
                    model_name='prophet',
                    run_id=run_future.id
                )
                db.session.add(forecast)
                forecast_created += 1
        
        db.session.commit()
        print(f"   ✅ Created {forecast_created} forecast records")
        
        # ============================================================
        # 5. CREATE MENU RECOMMENDATIONS
        # ============================================================
        print("\n💡 Creating menu recommendations...")
        
        menu_items = MenuItem.query.limit(10).all()
        recommendations_created = 0
        
        for item in menu_items:
            if item.margin_percent:
                score = min(item.margin_percent / 100.0, 1.0)
            else:
                score = 0.6
            
            rec = MenuRecommendation(
                menu_item_id=item.id,
                recommendation=f"High margin item '{item.name}' - consider promoting for better profitability. Current margin: {item.margin_percent:.1f}%",
                score=score,
                status='pending' if recommendations_created % 2 == 0 else 'accepted'
            )
            db.session.add(rec)
            recommendations_created += 1
        
        db.session.commit()
        print(f"   ✅ Created {recommendations_created} menu recommendations")
        
        # ============================================================
        # 6. CREATE COST OPTIMIZATIONS
        # ============================================================
        print("\n💰 Creating cost optimization suggestions...")
        
        menu_items = MenuItem.query.limit(5).all()
        optimizations_created = 0
        
        for item in menu_items:
            if item.cost_per_portion and item.selling_price:
                current_cost = float(item.cost_per_portion)
                # Suggest 5-10% cost reduction
                reduction_pct = 0.05 + (optimizations_created % 2) * 0.05
                suggested_cost = current_cost * (1 - reduction_pct)
                savings = current_cost - suggested_cost
                
                opt = CostOptimization(
                    menu_item_id=item.id,
                    suggestion_type='portion_tweak',
                    current_cost=Decimal(str(current_cost)),
                    suggested_cost=Decimal(str(suggested_cost)),
                    savings=Decimal(str(savings)),
                    details=f"Reduce portion size by {reduction_pct*100:.0f}% to save {savings:.0f} per serving",
                    status='pending'
                )
                db.session.add(opt)
                optimizations_created += 1
        
        db.session.commit()
        print(f"   ✅ Created {optimizations_created} cost optimizations")
        
        # ============================================================
        # 7. CREATE STAFFING SUGGESTIONS
        # ============================================================
        print("\n👥 Creating staffing suggestions...")
        
        events = Event.query.limit(5).all()
        staffing_created = 0
        
        for event in events:
            guest_count = event.guest_count or 50
            base_staff = max(2, guest_count // 10)
            chefs = max(1, base_staff // 3)
            waiters = max(2, base_staff - chefs)
            managers = 1
            
            roles_breakdown = {
                'chef': chefs,
                'waiter': waiters,
                'manager': managers
            }
            
            suggestion = StaffingSuggestion(
                event_id=event.id,
                date=event.event_date or date.today(),
                suggested_staff_count=sum(roles_breakdown.values()),
                roles_breakdown=json.dumps(roles_breakdown),
                confidence=0.75,
                status='pending' if staffing_created % 2 == 0 else 'accepted'
            )
            db.session.add(suggestion)
            staffing_created += 1
        
        db.session.commit()
        print(f"   ✅ Created {staffing_created} staffing suggestions")
        
        # ============================================================
        # 8. CREATE SHORTAGE ALERTS
        # ============================================================
        print("\n⚠️  Creating shortage alerts...")
        
        # Get inventory items with low stock
        inventory_items = InventoryItem.query.limit(10).all()
        alerts_created = 0
        
        for item in inventory_items:
            # Check stock levels - using stock_count for InventoryItem
            current_stock = float(item.stock_count) if item.stock_count else 0
            reorder_level = 20.0  # Default reorder level
            
            # Create alerts for items with low stock
            if current_stock < reorder_level:
                predicted_date = date.today() + timedelta(days=7)
                recommended_qty = max(reorder_level * 2, 50.0)
                
                # Determine severity
                if current_stock < reorder_level * 0.3:
                    severity = 'high'
                elif current_stock < reorder_level * 0.6:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                alert = ShortageAlert(
                    inventory_item_id=item.id,
                    predicted_shortage_date=predicted_date,
                    recommended_order_qty=recommended_qty,
                    severity=severity,
                    status='active'
                )
                db.session.add(alert)
                alerts_created += 1
        
        db.session.commit()
        print(f"   ✅ Created {alerts_created} shortage alerts")
        
        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "=" * 70)
        print("✅ AI Suite sample data seeded successfully!")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"   📋 Menu Items: {menu_items_created}")
        print(f"   📅 Events: {events_created}")
        print(f"   📦 Inventory Items: {inventory_created}")
        print(f"   📈 Forecast Records: {forecast_created}")
        print(f"   💡 Menu Recommendations: {recommendations_created}")
        print(f"   💰 Cost Optimizations: {optimizations_created}")
        print(f"   👥 Staffing Suggestions: {staffing_created}")
        print(f"   ⚠️  Shortage Alerts: {alerts_created}")
        
        print("\n🎉 Sample data ready for AI testing!")
        print("\n💡 Next steps:")
        print("   1. Navigate to /ai/dashboard to see all AI features")
        print("   2. Test menu recommendations at /ai/menu-recommendations")
        print("   3. Check cost optimizations at /ai/cost-optimizations")
        print("   4. View forecasts at /ai/forecast/POS")
        print("   5. Review shortage alerts at /ai/shortages")


if __name__ == "__main__":
    seed_ai_data()
