"""Seed sample data for POS system."""
from app import app, db
from datetime import datetime
from decimal import Decimal

from models import (
    POSDevice,
    POSShift,
    POSOrder,
    POSOrderLine,
    POSPayment,
    POSReceipt,
    User,
    UserRole,
    CateringItem,
    BakeryItem,
    PriceHistory,
)
from datetime import date

with app.app_context():
    print("Seeding POS sample data...")
    
    # Create sample POS devices
    devices_data = [
        {"name": "Main Counter Terminal", "code": "TERM-001", "location": "Main Reception"},
        {"name": "Kitchen POS Terminal", "code": "TERM-002", "location": "Kitchen"},
        {"name": "Drive-Through Terminal", "code": "TERM-003", "location": "Drive-Through Window"},
    ]
    
    for device_data in devices_data:
        existing = POSDevice.query.filter_by(terminal_code=device_data["code"]).first()
        if not existing:
            device = POSDevice(
                name=device_data["name"],
                terminal_code=device_data["code"],
                location=device_data["location"],
                is_active=True,
                last_seen=datetime.now(),
            )
            db.session.add(device)
            print(f"  Created device: {device_data['name']}")
    
    # Ensure we have catering and bakery items for POS
    if CateringItem.query.count() == 0:
        catering_items = [
            {"name": "Signature Plated Dinner", "price": 85000},
            {"name": "Live Cooking Station", "price": 65000},
            {"name": "Premium Buffet Spread", "price": 55000},
            {"name": "Cocktail Hour Bites", "price": 35000},
            {"name": "BBQ Platter", "price": 45000},
            {"name": "Vegetarian Delight", "price": 40000},
        ]
        
        for item_data in catering_items:
            item = CateringItem(name=item_data["name"])
            db.session.add(item)
            db.session.flush()
            
            # Create price history
            price_history = PriceHistory(
                item_id=item.id,
                item_type="CATERING",
                price_ugx=Decimal(str(item_data["price"])),
                effective_date=date.today(),
            )
            db.session.add(price_history)
            print(f"  Created catering item: {item_data['name']}")
    
    if BakeryItem.query.count() == 0:
        bakery_items = [
            {"name": "Vanilla Wedding Cake", "category": "Cake", "price": 350000},
            {"name": "Chocolate Dessert Bar", "category": "Dessert", "price": 150000},
            {"name": "Red Velvet Cake", "category": "Cake", "price": 280000},
            {"name": "Cupcake Assortment", "category": "Dessert", "price": 75000},
            {"name": "Birthday Cake (Small)", "category": "Cake", "price": 120000},
            {"name": "Birthday Cake (Large)", "category": "Cake", "price": 250000},
        ]
        
        for item_data in bakery_items:
            item = BakeryItem(
                name=item_data["name"],
                category=item_data["category"],
                status="Active",
            )
            db.session.add(item)
            db.session.flush()
            
            # Create price history
            price_history = PriceHistory(
                item_id=item.id,
                item_type="BAKERY",
                price_ugx=Decimal(str(item_data["price"])),
                effective_date=date.today(),
            )
            db.session.add(price_history)
            print(f"  Created bakery item: {item_data['name']}")
    
    db.session.commit()
    print("\nPOS sample data seeded successfully!")
    print("Sample devices created:")
    print("  - Main Counter Terminal (TERM-001)")
    print("  - Kitchen POS Terminal (TERM-002)")
    print("  - Drive-Through Terminal (TERM-003)")
    print("\nYou can now use the POS system with these terminals.")

