"""Add Ramadan/Iftar Special items to POS system."""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sas_management.app import create_app
from sas_management.models import db, POSProduct
from decimal import Decimal

def add_ramadan_iftar_items():
    """Add Ramadan/Iftar Special items to POS system."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Adding Ramadan/Iftar Special Items to POS")
        print("=" * 60)
        
        # Ramadan/Iftar Special Items (from SAS IFTAR SPECIAL poster; updated prices)
        ramadan_items = [
            # SAS IFTAR SPECIAL - LUSANIA
            {
                "name": "Lusania Single",
                "category": "Ramadan/Iftar",
                "price": 20000,
                "description": "SAS Iftar Lusania single: Rice, Irish/Gonja, Katogo, chapattis/Samosa/Vegetable wrap/Spring rolls, Steamed vegetables, Gravy, Avocado, Dates. Meat: Goat/Chicken."
            },
            {
                "name": "Lusania 3 People",
                "category": "Ramadan/Iftar",
                "price": 50000,
                "description": "SAS Iftar Lusania for 3: Rice, Chapati, Chicken, Goat, Katogo, Gravy, Fruit, Avocado, Samosas, Salads/Greens"
            },
            {
                "name": "Lusania 4 People",
                "category": "Ramadan/Iftar",
                "price": 75000,
                "description": "SAS Iftar Lusania for 4: Rice, Irish/Gonja, Katogo, chapattis/Samosa/Vegetable wrap/Spring rolls, Steamed vegetables, Gravy, Avocado, Dates. Meat: Goat/Chicken."
            },
            # IFTAR SPECIAL (Bundle) - legacy
            {
                "name": "Iftar Special (Bundle)",
                "category": "Ramadan/Iftar",
                "price": 20000,
                "description": "Complete Iftar bundle: Rice, Chicken/Goat Meat, Irish, Chapati/Samosa, Katogo, Gravy, Fruits, Dates"
            },
            # SAS IFTAR SPECIAL - DAAKU SPECIAL
            {
                "name": "Paratha Chapats (25 PCS)",
                "category": "Ramadan/Iftar",
                "price": 50000,
                "description": "Fresh paratha chapattis - 25 pieces"
            },
            {
                "name": "Ordinary Chapats (25 PCS)",
                "category": "Ramadan/Iftar",
                "price": 35000,
                "description": "Ordinary chapattis - 25 pieces"
            },
            # Individual items from poster
            {
                "name": "Paratha (25 PCS)",
                "category": "Ramadan/Iftar",
                "price": 50000,
                "description": "Fresh paratha - 25 pieces"
            },
            {
                "name": "Parotas",
                "category": "Ramadan/Iftar",
                "price": 50000,
                "description": "Parotas - folded flatbreads"
            },
            {
                "name": "Fish Platter",
                "category": "Ramadan/Iftar",
                "price": 50000,
                "description": "Grilled fish platter with lemon and herbs"
            },
            {
                "name": "Whole Fish (Tilapia)",
                "category": "Ramadan/Iftar",
                "price": 50000,
                "description": "Whole fresh tilapia fish"
            },
            {
                "name": "SAS Rice Box (Chicken/Goat Meat)",
                "category": "Ramadan/Iftar",
                "price": 55000,
                "description": "SAS special rice box with choice of chicken or goat meat"
            },
            {
                "name": "Normal Chapati (25 PCS)",
                "category": "Ramadan/Iftar",
                "price": 35000,
                "description": "Fresh normal chapati - 25 pieces"
            },
            {
                "name": "Lusania for 3 People",
                "category": "Ramadan/Iftar",
                "price": 50000,
                "description": "Complete Lusania meal for 3 people: Rice, Chapati, Chicken, Goat, Katogo, Gravy, Fruit, Avocado, Samosas, Salads/Greens"
            },
            
            # Individual components (for flexibility)
            {
                "name": "Rice",
                "category": "Ramadan/Iftar",
                "price": 5000,
                "description": "Steamed rice"
            },
            {
                "name": "Chicken Meat",
                "category": "Ramadan/Iftar",
                "price": 8000,
                "description": "Chicken meat"
            },
            {
                "name": "Goat Meat",
                "category": "Ramadan/Iftar",
                "price": 10000,
                "description": "Goat meat"
            },
            {
                "name": "Irish",
                "category": "Ramadan/Iftar",
                "price": 3000,
                "description": "Irish potatoes"
            },
            {
                "name": "Chapati",
                "category": "Ramadan/Iftar",
                "price": 1500,
                "description": "Fresh chapati (per piece)"
            },
            {
                "name": "Samosa",
                "category": "Ramadan/Iftar",
                "price": 2000,
                "description": "Fried samosa (per piece)"
            },
            {
                "name": "Katogo",
                "category": "Ramadan/Iftar",
                "price": 4000,
                "description": "Katogo (Ugandan dish)"
            },
            {
                "name": "Gravy",
                "category": "Ramadan/Iftar",
                "price": 3000,
                "description": "Gravy sauce"
            },
            {
                "name": "Fruits",
                "category": "Ramadan/Iftar",
                "price": 5000,
                "description": "Fresh fruits"
            },
            {
                "name": "Dates",
                "category": "Ramadan/Iftar",
                "price": 5000,
                "description": "Fresh dates"
            },
            {
                "name": "Avocado",
                "category": "Ramadan/Iftar",
                "price": 3000,
                "description": "Fresh avocado"
            },
            {
                "name": "Salads/Greens",
                "category": "Ramadan/Iftar",
                "price": 4000,
                "description": "Fresh salads and greens"
            },
        ]
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        print("\n[1/1] Creating Ramadan/Iftar POS Products...")
        
        for product_data in ramadan_items:
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
                    description=product_data.get("description", ""),
                    is_available=True,
                    is_active=True,
                )
                db.session.add(product)
                created_count += 1
                print(f"  [OK] Created: {product.name} - UGX {product_data['price']:,}")
            else:
                # Update existing product if price or description changed
                if existing.price != Decimal(str(product_data["price"])) or existing.description != product_data.get("description", ""):
                    existing.price = Decimal(str(product_data["price"]))
                    existing.description = product_data.get("description", "")
                    existing.is_available = True
                    existing.is_active = True
                    updated_count += 1
                    print(f"  [UPDATE] Updated: {existing.name} - UGX {product_data['price']:,}")
                else:
                    skipped_count += 1
                    print(f"  [SKIP] Already exists: {product_data['name']}")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("SUCCESS!")
            print("=" * 60)
            print(f"\n[OK] New Products Created: {created_count}")
            if updated_count > 0:
                print(f"[OK] Products Updated: {updated_count}")
            if skipped_count > 0:
                print(f"[SKIP] Products Skipped (already exist): {skipped_count}")
            
            # Count total Ramadan/Iftar items
            total_ramadan_items = POSProduct.query.filter_by(category="Ramadan/Iftar", is_available=True).count()
            print(f"\nTotal Ramadan/Iftar Products Available: {total_ramadan_items}")
            print("\nYou can now:")
            print("  1. Go to POS System -> Open Terminal")
            print("  2. Select a terminal")
            print("  3. Start a shift and select 'Ramadan/Iftar' category")
            print("  4. Click items to add to cart and process orders!")
            print("\n" + "=" * 60)
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Failed to save data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == "__main__":
    success = add_ramadan_iftar_items()
    sys.exit(0 if success else 1)
