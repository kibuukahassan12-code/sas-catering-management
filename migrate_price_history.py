"""
Migration script to move existing price data from CateringItem and BakeryItem
to the new PriceHistory table.

Run this script once after deploying the price versioning system.
"""
from app import app, db
from models import CateringItem, BakeryItem, PriceHistory, User
from datetime import date
from decimal import Decimal

def migrate_prices():
    """Migrate existing prices to PriceHistory table."""
    with app.app_context():
        print("Starting price history migration...")
        
        # Check if old columns exist
        try:
            db.session.execute(db.text("SELECT selling_price_ugx FROM catering_item LIMIT 1"))
            catering_column_exists = True
        except Exception:
            catering_column_exists = False
        
        try:
            db.session.execute(db.text("SELECT unit_price_ugx FROM bakery_item LIMIT 1"))
            bakery_column_exists = True
        except Exception:
            bakery_column_exists = False
        
        # Migrate CateringItem prices
        catering_items = CateringItem.query.all()
        migrated_catering = 0
        skipped_catering = 0
        for item in catering_items:
            # Check if price history already exists
            existing = PriceHistory.query.filter_by(
                item_id=item.id, 
                item_type="CATERING"
            ).first()
            
            if existing:
                skipped_catering += 1
                continue
            
            old_price = Decimal("0.00")
            if catering_column_exists:
                try:
                    result = db.session.execute(
                        db.text("SELECT selling_price_ugx FROM catering_item WHERE id = :id"),
                        {"id": item.id}
                    ).fetchone()
                    if result and result[0] is not None:
                        old_price = Decimal(str(result[0]))
                except Exception as e:
                    print(f"Warning: Could not read price for CateringItem {item.id}: {e}")
            
            # Create price history record even if price is 0 (for items without prices)
            price_history = PriceHistory(
                item_id=item.id,
                item_type="CATERING",
                price_ugx=old_price,
                effective_date=date.today(),
                user_id=None  # Migration - no user context
            )
            db.session.add(price_history)
            if old_price > 0:
                migrated_catering += 1
        
        # Migrate BakeryItem prices
        bakery_items = BakeryItem.query.all()
        migrated_bakery = 0
        skipped_bakery = 0
        for item in bakery_items:
            # Check if price history already exists
            existing = PriceHistory.query.filter_by(
                item_id=item.id, 
                item_type="BAKERY"
            ).first()
            
            if existing:
                skipped_bakery += 1
                continue
            
            old_price = Decimal("0.00")
            if bakery_column_exists:
                try:
                    result = db.session.execute(
                        db.text("SELECT unit_price_ugx FROM bakery_item WHERE id = :id"),
                        {"id": item.id}
                    ).fetchone()
                    if result and result[0] is not None:
                        old_price = Decimal(str(result[0]))
                except Exception as e:
                    print(f"Warning: Could not read price for BakeryItem {item.id}: {e}")
            
            # Create price history record even if price is 0 (for items without prices)
            price_history = PriceHistory(
                item_id=item.id,
                item_type="BAKERY",
                price_ugx=old_price,
                effective_date=date.today(),
                user_id=None  # Migration - no user context
            )
            db.session.add(price_history)
            if old_price > 0:
                migrated_bakery += 1
        
        db.session.commit()
        print(f"Migration complete!")
        print(f"  - Migrated {migrated_catering} CateringItem prices (skipped {skipped_catering} with existing history)")
        print(f"  - Migrated {migrated_bakery} BakeryItem prices (skipped {skipped_bakery} with existing history)")
        if not catering_column_exists and not bakery_column_exists:
            print("  - Note: Old price columns not found in database (already removed or never existed)")

if __name__ == "__main__":
    migrate_prices()

