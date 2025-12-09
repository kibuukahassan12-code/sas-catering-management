"""Seed BI module with sample data."""
from app import create_app
from models import (
    db, BIIngredientPriceTrend, BIPOSHeatmap, BISalesForecast,
    BIEventProfitability, BIBakeryDemand, Ingredient, Event, BakeryItem
)
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

def seed_bi_data():
    """Seed BI sample data."""
    app = create_app()
    
    with app.app_context():
        try:
            print("Seeding BI sample data...")
            
            # 1. Seed Ingredient Price Trends (last 7 days for 3 ingredients)
            ingredients = Ingredient.query.limit(3).all()
            if ingredients:
                print(f"  Adding price trends for {len(ingredients)} ingredients...")
                for ingredient in ingredients:
                    base_price = float(ingredient.unit_cost_ugx or 5000)
                    for i in range(7):
                        price_date = date.today() - timedelta(days=6-i)
                        # Add some random variation (±10%)
                        variation = random.uniform(-0.10, 0.10)
                        price = base_price * (1 + variation)
                        
                        existing = BIIngredientPriceTrend.query.filter_by(
                            inventory_item_id=ingredient.id,
                            date=price_date
                        ).first()
                        
                        if not existing:
                            trend = BIIngredientPriceTrend(
                                inventory_item_id=ingredient.id,
                                date=price_date,
                                price=price
                            )
                            db.session.add(trend)
                print("    ✓ Ingredient price trends added")
            else:
                print("    ⚠️  No ingredients found - skipping price trends")
            
            # 2. Seed POS Heatmap (7 days × 24 hours)
            print("  Adding POS heatmap data...")
            days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            end_date = date.today()
            start_date = end_date - timedelta(days=6)
            
            for day_idx, day_name in enumerate(days_of_week):
                for hour in range(24):
                    # Peak hours: 8-10, 12-14, 17-19
                    if hour in [8, 9, 12, 13, 17, 18]:
                        base_sales = 15000.0
                        base_count = 3
                    elif hour in [10, 11, 14, 15, 19, 20]:
                        base_sales = 10000.0
                        base_count = 2
                    else:
                        base_sales = 3000.0
                        base_count = 1
                    
                    # Weekend boost
                    if day_idx >= 5:
                        base_sales *= 1.5
                        base_count = int(base_count * 1.5)
                    
                    existing = BIPOSHeatmap.query.filter_by(
                        day=day_name,
                        hour=hour,
                        period_start=start_date,
                        period_end=end_date
                    ).first()
                    
                    if not existing:
                        heatmap = BIPOSHeatmap(
                            day=day_name,
                            hour=hour,
                            sales=base_sales,
                            transaction_count=base_count,
                            period_start=start_date,
                            period_end=end_date
                        )
                        db.session.add(heatmap)
            print("    ✓ POS heatmap data added")
            
            # 3. Seed Sales Forecast (next 14 days)
            print("  Adding sales forecasts...")
            forecast_date = date.today() + timedelta(days=1)
            sources = ["POS", "Catering", "Bakery"]
            
            for source in sources:
                base_avg = {"POS": 50000, "Catering": 100000, "Bakery": 30000}[source]
                
                for i in range(14):
                    forecast_day = forecast_date + timedelta(days=i)
                    day_of_week = forecast_day.weekday()
                    
                    # Day-of-week adjustment
                    multiplier = 1.5 if day_of_week >= 5 else 1.0
                    predicted = base_avg * multiplier * random.uniform(0.9, 1.1)
                    
                    existing = BISalesForecast.query.filter_by(
                        source=source,
                        date=forecast_day
                    ).first()
                    
                    if not existing:
                        forecast = BISalesForecast(
                            source=source,
                            date=forecast_day,
                            predicted_sales=predicted,
                            model_name="simple",
                            confidence=0.7
                        )
                        db.session.add(forecast)
            print("    ✓ Sales forecasts added")
            
            # 4. Seed one Event Profitability (if events exist)
            completed_event = Event.query.filter_by(status="Completed").first()
            if completed_event:
                existing_prof = BIEventProfitability.query.filter_by(event_id=completed_event.id).first()
                if not existing_prof:
                    revenue = float(completed_event.quoted_value or 500000)
                    cogs = float(completed_event.actual_cogs_ugx or revenue * 0.4)
                    labor = 400000.0
                    overhead = revenue * 0.10
                    profit = revenue - cogs - labor - overhead
                    margin = (profit / revenue * 100) if revenue > 0 else 0
                    
                    profitability = BIEventProfitability(
                        event_id=completed_event.id,
                        revenue=revenue,
                        cost_of_goods=cogs,
                        labor_cost=labor,
                        overhead_cost=overhead,
                        profit=profit,
                        margin_percent=margin
                    )
                    db.session.add(profitability)
                    print("    ✓ Event profitability sample added")
            else:
                print("    ⚠️  No completed events found - skipping profitability")
            
            # 5. Seed Bakery Demand Forecast (for one item, next 7 days)
            bakery_item = BakeryItem.query.filter_by(status="Active").first()
            if bakery_item:
                forecast_date = date.today() + timedelta(days=1)
                for i in range(7):
                    forecast_day = forecast_date + timedelta(days=i)
                    day_of_week = forecast_day.weekday()
                    multiplier = 1.8 if day_of_week >= 5 else 1.0
                    predicted_qty = int(5 * multiplier * random.uniform(0.8, 1.2))
                    
                    existing = BIBakeryDemand.query.filter_by(
                        bakery_item_id=bakery_item.id,
                        date=forecast_day
                    ).first()
                    
                    if not existing:
                        demand = BIBakeryDemand(
                            bakery_item_id=bakery_item.id,
                            date=forecast_day,
                            predicted_qty=predicted_qty,
                            model_name="simple",
                            confidence=0.65
                        )
                        db.session.add(demand)
                print("    ✓ Bakery demand forecast added")
            else:
                print("    ⚠️  No bakery items found - skipping demand forecast")
            
            db.session.commit()
            print("\n✅ BI sample data seeded successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error seeding BI data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    seed_bi_data()

