#!/usr/bin/env python3
"""
Add comprehensive sample data to POS system
Creates sample orders, shifts, payments, and receipts
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

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
    Client,
)

def generate_reference(prefix="POS"):
    """Generate a unique order reference."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(100, 999)
    return f"{prefix}-{timestamp}-{random_num}"

def add_pos_sample_data():
    """Add comprehensive sample data to POS system."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("ADDING POS SAMPLE DATA")
        print("=" * 60)
        print()
        
        # Get required data
        devices = POSDevice.query.filter_by(is_active=True).all()
        if not devices:
            print("❌ No POS devices found. Please run restore_pos_system.py first.")
            return False
        
        products = POSProduct.query.all()
        catering_items = []
        bakery_items = []
        
        try:
            from models import CateringItem, BakeryItem
            catering_items = CateringItem.query.limit(5).all()
            bakery_items = BakeryItem.query.filter_by(status="Active").limit(5).all()
        except:
            pass
        
        users = User.query.limit(3).all()
        if not users:
            print("❌ No users found. Please create users first.")
            return False
        
        clients = Client.query.limit(5).all()
        walk_in_client = Client.query.filter_by(name="Walk-in Customer").first()
        if not walk_in_client and clients:
            walk_in_client = clients[0]
        
        print(f"Found: {len(devices)} devices, {len(products)} POS products, {len(users)} users")
        print()
        
        # Create sample shifts
        print("1. Creating sample shifts...")
        shifts_created = 0
        for i, device in enumerate(devices[:2]):  # Use first 2 devices
            user = users[i % len(users)]
            
            # Create a closed shift from yesterday
            yesterday = datetime.now() - timedelta(days=1)
            shift = POSShift(
                device_id=device.id,
                user_id=user.id,
                starting_cash=Decimal("100000"),
                ending_cash=Decimal("250000"),
                status="closed",
                started_at=yesterday.replace(hour=8, minute=0),
                ended_at=yesterday.replace(hour=17, minute=0),
            )
            db.session.add(shift)
            db.session.flush()
            shifts_created += 1
            
            # Create orders for this shift
            for order_num in range(3):
                order_time = yesterday.replace(hour=9 + order_num * 2, minute=random.randint(0, 59))
                
                # Create order
                order = POSOrder(
                    device_id=device.id,
                    shift_id=shift.id,
                    client_id=walk_in_client.id if walk_in_client else None,
                    reference=generate_reference(),
                    order_time=order_time,
                    total_amount=Decimal("0"),
                    tax_amount=Decimal("0"),
                    discount_amount=Decimal("0"),
                    status="paid",
                    is_delivery=random.choice([True, False]),
                )
                db.session.add(order)
                db.session.flush()
                
                # Add order lines
                num_items = random.randint(2, 5)
                subtotal = Decimal("0")
                
                for _ in range(num_items):
                    # Mix POS products, catering, and bakery items
                    item_type = random.choice(["pos", "catering", "bakery"])
                    
                    if item_type == "pos" and products:
                        product = random.choice(products)
                        qty = random.randint(1, 3)
                        unit_price = Decimal(str(product.price))
                        line_total = unit_price * qty
                        subtotal += line_total
                        
                        line = POSOrderLine(
                            order_id=order.id,
                            product_id=product.id,
                            product_name=product.name,
                            qty=qty,
                            unit_price=unit_price,
                            line_total=line_total,
                        )
                        db.session.add(line)
                    
                    elif item_type == "catering" and catering_items:
                        item = random.choice(catering_items)
                        qty = random.randint(1, 2)
                        try:
                            unit_price = Decimal(str(item.get_current_price() or 50000))
                        except:
                            unit_price = Decimal("50000")
                        line_total = unit_price * qty
                        subtotal += line_total
                        
                        line = POSOrderLine(
                            order_id=order.id,
                            product_id=None,
                            product_name=item.name,
                            qty=qty,
                            unit_price=unit_price,
                            line_total=line_total,
                        )
                        db.session.add(line)
                    
                    elif item_type == "bakery" and bakery_items:
                        item = random.choice(bakery_items)
                        qty = random.randint(1, 2)
                        try:
                            unit_price = Decimal(str(item.get_current_price() or 100000))
                        except:
                            unit_price = Decimal("100000")
                        line_total = unit_price * qty
                        subtotal += line_total
                        
                        line = POSOrderLine(
                            order_id=order.id,
                            product_id=None,
                            product_name=item.name,
                            qty=qty,
                            unit_price=unit_price,
                            line_total=line_total,
                        )
                        db.session.add(line)
                
                # Calculate tax and total
                tax_amount = subtotal * Decimal("0.18")
                total_amount = subtotal + tax_amount
                
                order.total_amount = total_amount
                order.tax_amount = tax_amount
                
                # Create payment
                payment = POSPayment(
                    order_id=order.id,
                    amount=total_amount,
                    method=random.choice(["cash", "card", "mobile_money"]),
                )
                db.session.add(payment)
                db.session.flush()
                
                # Create receipt
                receipt = POSReceipt(
                    order_id=order.id,
                    receipt_number=generate_reference("RCP"),
                )
                db.session.add(receipt)
        
        print(f"   ✓ Created {shifts_created} shifts with orders")
        
        # Create today's open shift
        print("\n2. Creating today's open shift...")
        device = devices[0]
        user = users[0]
        
        existing_shift = POSShift.query.filter_by(
            device_id=device.id,
            user_id=user.id,
            status="open"
        ).first()
        
        if not existing_shift:
            today_shift = POSShift(
                device_id=device.id,
                user_id=user.id,
                starting_cash=Decimal("50000"),
                status="open",
                started_at=datetime.now().replace(hour=8, minute=0),
            )
            db.session.add(today_shift)
            print("   ✓ Created open shift for today")
        else:
            print("   - Open shift already exists")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ POS SAMPLE DATA ADDED SUCCESSFULLY")
            print("=" * 60)
            print("\nCreated:")
            print(f"  - {shifts_created} closed shifts with orders")
            print(f"  - Multiple sample orders with payments and receipts")
            print("\nYou can now view the POS dashboard to see the data.")
            print()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = add_pos_sample_data()
    sys.exit(0 if success else 1)

