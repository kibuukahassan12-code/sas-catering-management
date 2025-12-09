#!/usr/bin/env python3
"""
Restore POS System with Sample Data
Creates devices, sample products, and ensures all features work
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import (
    POSDevice,
    POSProduct,
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
    Client,
)

def restore_pos_system():
    """Restore POS system with sample data."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("POS SYSTEM RESTORATION")
        print("=" * 60)
        print()
        
        # 1. Create POS Devices
        print("1. Creating POS Devices...")
        devices_data = [
            {"name": "Main Counter Terminal", "code": "TERM-001", "location": "Main Reception"},
            {"name": "Kitchen POS Terminal", "code": "TERM-002", "location": "Kitchen"},
            {"name": "Drive-Through Terminal", "code": "TERM-003", "location": "Drive-Through Window"},
            {"name": "Mobile POS Terminal", "code": "TERM-004", "location": "Mobile Service"},
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
                print(f"   ✓ Created device: {device_data['name']} ({device_data['code']})")
            else:
                print(f"   - Device already exists: {device_data['name']}")
        
        # 2. Create Sample POS Products
        print("\n2. Creating Sample POS Products...")
        pos_products_data = [
            {"name": "Coffee - Espresso", "category": "Beverages", "price": 5000, "description": "Single shot espresso"},
            {"name": "Coffee - Cappuccino", "category": "Beverages", "price": 8000, "description": "Espresso with steamed milk"},
            {"name": "Coffee - Latte", "category": "Beverages", "price": 9000, "description": "Espresso with milk foam"},
            {"name": "Tea - English Breakfast", "category": "Beverages", "price": 4000, "description": "Classic English tea"},
            {"name": "Fresh Juice - Orange", "category": "Beverages", "price": 6000, "description": "Freshly squeezed orange juice"},
            {"name": "Fresh Juice - Mango", "category": "Beverages", "price": 7000, "description": "Fresh mango juice"},
            {"name": "Bottled Water", "category": "Beverages", "price": 2000, "description": "500ml bottled water"},
            {"name": "Soft Drink", "category": "Beverages", "price": 3000, "description": "Carbonated soft drink"},
            {"name": "Sandwich - Chicken", "category": "Food", "price": 15000, "description": "Grilled chicken sandwich"},
            {"name": "Sandwich - Veggie", "category": "Food", "price": 12000, "description": "Vegetable sandwich"},
            {"name": "Salad - Garden", "category": "Food", "price": 18000, "description": "Fresh garden salad"},
            {"name": "Soup - Daily Special", "category": "Food", "price": 14000, "description": "Chef's daily soup"},
        ]
        
        for product_data in pos_products_data:
            existing = POSProduct.query.filter_by(name=product_data["name"]).first()
            if not existing:
                product = POSProduct(
                    name=product_data["name"],
                    category=product_data["category"],
                    price=Decimal(str(product_data["price"])),
                    is_available=True,
                )
                db.session.add(product)
                print(f"   ✓ Created product: {product_data['name']}")
            else:
                print(f"   - Product already exists: {product_data['name']}")
        
        # 3. Ensure we have at least one user
        print("\n3. Checking users...")
        admin_user = User.query.filter_by(role=UserRole.Admin).first()
        if not admin_user:
            print("   ⚠️  No admin user found. Please create a user first.")
        else:
            print(f"   ✓ Found admin user: {admin_user.email}")
        
        # 4. Create sample client if none exists
        print("\n4. Checking clients...")
        if Client.query.count() == 0:
            client = Client(
                name="Walk-in Customer",
                contact_person="N/A",
                phone="0000000000",
                email="walkin@example.com",
            )
            db.session.add(client)
            print("   ✓ Created sample walk-in client")
        else:
            print(f"   ✓ Found {Client.query.count()} client(s)")
        
        # 5. Ensure catering and bakery items have prices
        print("\n5. Ensuring catering and bakery items have prices...")
        catering_count = 0
        for item in CateringItem.query.all():
            if not item.get_current_price():
                price_history = PriceHistory(
                    item_id=item.id,
                    item_type="CATERING",
                    price_ugx=Decimal("50000"),
                    effective_date=date.today(),
                )
                db.session.add(price_history)
                catering_count += 1
        if catering_count > 0:
            print(f"   ✓ Added prices to {catering_count} catering items")
        
        bakery_count = 0
        for item in BakeryItem.query.all():
            if not item.get_current_price():
                price_history = PriceHistory(
                    item_id=item.id,
                    item_type="BAKERY",
                    price_ugx=Decimal("100000"),
                    effective_date=date.today(),
                )
                db.session.add(price_history)
                bakery_count += 1
        if bakery_count > 0:
            print(f"   ✓ Added prices to {bakery_count} bakery items")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ POS SYSTEM RESTORATION COMPLETE")
            print("=" * 60)
            print("\nCreated:")
            print(f"  - {len(devices_data)} POS devices")
            print(f"  - {len(pos_products_data)} POS products")
            print("\nYou can now:")
            print("  1. Visit /pos/ to see available terminals")
            print("  2. Open a terminal and start a shift")
            print("  3. Process orders and payments")
            print()
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    success = restore_pos_system()
    sys.exit(0 if success else 1)

