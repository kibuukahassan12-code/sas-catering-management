"""
SAS MANAGEMENT SYSTEM – ADD EVENT PACKAGES (SAFE SEED)
RULES:
- NO schema changes
- NO deletions
- NO overwrites
- Add only if missing
"""

import sys
import os
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import MenuPackage, db


def add_package(name, price, description):
    """
    Add a menu package only if it doesn't already exist.
    Safe operation - checks by name before adding.
    """
    # Check if package already exists by name (case-insensitive check)
    exists = MenuPackage.query.filter(
        db.func.lower(MenuPackage.name) == name.lower()
    ).first()
    
    if exists:
        print(f"[SKIP] Package already exists: {name}")
        return False
    
    # Create new package
    # Note: MenuPackage model has: name, price_per_guest (Float), description, items
    # price_per_guest cannot be None, so use 0.0 for negotiable prices
    package = MenuPackage(
        name=name,
        price_per_guest=float(price) if price is not None else 0.0,
        description=description,
    )
    db.session.add(package)
    price_display = f"UGX {price:,.0f}" if price else "Negotiable (0.0)"
    print(f"[ADD] Package created: {name} (Price: {price_display})")
    return True


def seed_event_packages():
    """Seed event packages - only adds missing packages."""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("SEEDING EVENT PACKAGES (SAFE MODE)")
        print("=" * 70)
        print()
        
        try:
            # Check existing packages count
            existing_count = MenuPackage.query.count()
            print(f"Existing packages in database: {existing_count}")
            print()
            
            # Define packages to add
            packages = [
                # Cakes & Desserts
                ("Dessert Cake Package", 250000,
                 "Premium baked cakes decorated with elegance. Ideal for weddings, corporate events, and private celebrations. Available in vanilla, chocolate, red velvet, and fruit-filled layers."),

                # Fruits
                ("Fruit Package", None,
                 "Vibrant, refreshing assorted fruits beautifully prepared to add color, health, and freshness to your event. Price is negotiable."),

                # Ramadan
                ("Ramathan Package", 25000,
                 "A daily iftar meal plan designed to provide delicious, balanced, and refreshing dishes that honor the spirit of fasting and fellowship."),

                # Traditional
                ("Stuffed Pumpkin Package", 100000,
                 "Carefully selected pumpkin roasted to perfection and stuffed with a rich variety of traditional fillings."),

                ("Whole Goat Package", 1000000,
                 "A perfectly roasted whole goat prepared for celebrations where tradition meets togetherness. Price may vary depending on size."),

                ("Luwombo Package", 100000,
                 "Exclusive Mukolo Luwombo prepared using traditional methods. A meaningful cultural dish specially prepared for the groom (Omuko)."),

                # Setup & Corporate
                ("Set-Up Package", 2000000,
                 "High-end buffet setup providing sophistication, style, and strong visual impact for your event. Pricing starts from 2M and above."),

                ("Corporate Package", None,
                 "Consistent, high-quality corporate catering for meetings, conferences, and long-term staff meal plans. Pricing is negotiable."),

                # BBQ
                ("BBQ Package", 25000,
                 "Freshly grilled meats prepared on-site. Nothing brings people together like the aroma of a great barbecue."),

                # Tiered Packages
                ("Standard Package", 35000,
                 "Accessible, well-balanced menu ideal for small gatherings, birthdays, office lunches, and celebrations."),

                ("Premium Package", 50000,
                 "Enhanced dining experience with refined menu options and elevated presentation. Perfect for weddings and conferences."),

                ("Executive Package", 100000,
                 "Top-tier luxury catering for high-profile events and grand occasions. Includes premium presentation and VIP food setup."),

                # Labour Package
                ("Labour Package", None,
                 "Professional staffing services for events including wait staff, bartenders, kitchen assistants, security personnel, and event coordinators. Our experienced team ensures smooth event execution with proper service standards. Pricing is negotiable based on event size, duration, and specific requirements. Includes training on service protocols and event-specific needs."),
            ]
            
            added_count = 0
            skipped_count = 0
            
            print("Processing packages...")
            print("-" * 70)
            
            for name, price, description in packages:
                if add_package(name, price, description):
                    added_count += 1
                else:
                    skipped_count += 1
            
            print("-" * 70)
            print(f"\nProcessing complete:")
            print(f"  [OK] Added: {added_count} new packages")
            print(f"  [SKIP] Skipped: {skipped_count} existing packages")
            
            # Commit only if there are changes
            if added_count > 0:
                db.session.commit()
                print(f"\n[SUCCESS] Successfully added {added_count} new package(s) to database.")
            else:
                print("\n[INFO] All packages already exist. No changes made.")
            
            # Show final count
            final_count = MenuPackage.query.count()
            print(f"\nTotal packages in database: {final_count}")
            print("=" * 70)
            print()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Failed to seed event packages: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = seed_event_packages()
    sys.exit(0 if success else 1)
