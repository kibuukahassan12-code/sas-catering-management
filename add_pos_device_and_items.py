"""Add POS device and sample items ready for sale."""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sas_management.app import create_app
from sas_management.models import db, POSDevice, POSProduct, User
from datetime import datetime
from decimal import Decimal

def add_pos_device_and_items():
    """Add a POS device and sample items ready for sale."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Adding POS Device and Sample Items")
        print("=" * 60)
        
        # 1. Add POS Device
        print("\n[1/2] Creating POS Device...")
        device_code = "TERM-001"
        device = POSDevice.query.filter_by(terminal_code=device_code).first()
        
        if not device:
            device = POSDevice(
                name="Main Counter Terminal",
                terminal_code=device_code,
                location="Main Store",
                is_active=True,
                last_seen=datetime.now(),
            )
            db.session.add(device)
            db.session.flush()
            print(f"  [OK] Created device: {device.name} ({device.terminal_code})")
        else:
            print(f"  [SKIP] Device already exists: {device.name} ({device.terminal_code})")
        
        # 2. Add Sample POS Products
        print("\n[2/2] Creating Sample POS Products...")
        
        sample_products = [
            # Beverages
            {"name": "Coffee (Regular)", "category": "Beverages", "price": 5000, "description": "Hot coffee"},
            {"name": "Coffee (Cappuccino)", "category": "Beverages", "price": 8000, "description": "Espresso with steamed milk"},
            {"name": "Tea (Black)", "category": "Beverages", "price": 3000, "description": "Hot black tea"},
            {"name": "Fresh Juice", "category": "Beverages", "price": 6000, "description": "Fresh fruit juice"},
            {"name": "Soft Drink", "category": "Beverages", "price": 4000, "description": "Carbonated soft drink"},
            {"name": "Bottled Water", "category": "Beverages", "price": 2000, "description": "500ml bottled water"},
            
            # Snacks
            {"name": "Samosa", "category": "Snacks", "price": 2000, "description": "Fried pastry with filling"},
            {"name": "Chapati", "category": "Snacks", "price": 1500, "description": "Flatbread"},
            {"name": "Mandazi", "category": "Snacks", "price": 1500, "description": "Sweet fried dough"},
            {"name": "Roasted Peanuts", "category": "Snacks", "price": 3000, "description": "Roasted groundnuts"},
            {"name": "Chips", "category": "Snacks", "price": 2500, "description": "Potato chips"},
            
            # Meals
            {"name": "Rice & Beans", "category": "Meals", "price": 8000, "description": "Steamed rice with beans"},
            {"name": "Matoke", "category": "Meals", "price": 10000, "description": "Steamed plantains"},
            {"name": "Chicken Stew", "category": "Meals", "price": 15000, "description": "Chicken in sauce"},
            {"name": "Beef Stew", "category": "Meals", "price": 18000, "description": "Beef in sauce"},
            {"name": "Fish & Chips", "category": "Meals", "price": 20000, "description": "Fried fish with chips"},
            {"name": "Vegetable Plate", "category": "Meals", "price": 12000, "description": "Mixed vegetables"},
            
            # Bakery Items
            {"name": "Bread (White)", "category": "Bakery", "price": 3000, "description": "Fresh white bread"},
            {"name": "Bread (Brown)", "category": "Bakery", "price": 3500, "description": "Whole wheat bread"},
            {"name": "Doughnut", "category": "Bakery", "price": 2000, "description": "Glazed doughnut"},
            {"name": "Cookie", "category": "Bakery", "price": 1500, "description": "Chocolate chip cookie"},
            {"name": "Muffin", "category": "Bakery", "price": 4000, "description": "Blueberry muffin"},
            
            # Desserts
            {"name": "Ice Cream (Scoop)", "category": "Desserts", "price": 5000, "description": "Single scoop ice cream"},
            {"name": "Cake Slice", "category": "Desserts", "price": 8000, "description": "Slice of cake"},
            {"name": "Fruit Salad", "category": "Desserts", "price": 6000, "description": "Mixed fresh fruits"},
        ]
        
        created_count = 0
        skipped_count = 0
        
        for product_data in sample_products:
            # Check if product already exists
            existing = POSProduct.query.filter_by(
                name=product_data["name"],
                category=product_data["category"]
            ).first()
            
            if not existing:
                product = POSProduct(
                    name=product_data["name"],
                    category=product_data["category"],
                    price=Decimal(str(product_data["price"])),
                    is_available=True,
                )
                db.session.add(product)
                created_count += 1
                print(f"  [OK] Created: {product.name} - {product_data['category']} - UGX {product_data['price']:,}")
            else:
                skipped_count += 1
                print(f"  [SKIP] Already exists: {product_data['name']}")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("SUCCESS!")
            print("=" * 60)
            print(f"\n[OK] POS Device: {device.name} ({device.terminal_code})")
            print(f"[OK] Sample Products Created: {created_count}")
            if skipped_count > 0:
                print(f"[SKIP] Products Skipped (already exist): {skipped_count}")
            print(f"\nTotal Products Ready for Sale: {POSProduct.query.filter_by(is_available=True).count()}")
            print("\nYou can now:")
            print("  1. Go to POS System -> Open Terminal")
            print("  2. Select the terminal: TERM-001")
            print("  3. Start a shift and begin selling!")
            print("\n" + "=" * 60)
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Failed to save data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == "__main__":
    success = add_pos_device_and_items()
    sys.exit(0 if success else 1)

