"""
Complete POS System Setup Script
Creates terminals, products, sample orders, shifts, and makes POS fully functional.

Usage:
    python setup_pos_system.py
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import (
    POSDevice,
    POSProduct,
    POSShift,
    POSOrder,
    POSOrderLine,
    POSPayment,
    POSReceipt,
    User,
    Client,
    db
)


def generate_order_reference(prefix="POS"):
    """Generate a unique order reference."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(100, 999)
    return f"{prefix}-{timestamp}-{random_num}"


def create_pos_terminals():
    """Create POS terminals/devices."""
    print("\n1. Creating POS Terminals...")
    
    terminals_data = [
        {
            "name": "Main Counter Terminal",
            "terminal_code": "TERM-001",
            "location": "Main Store - Front Counter",
        },
        {
            "name": "Drive-Through Terminal",
            "terminal_code": "TERM-002",
            "location": "Drive-Through Window",
        },
        {
            "name": "Event Counter Terminal",
            "terminal_code": "TERM-003",
            "location": "Event Service Counter",
        },
    ]
    
    created_terminals = []
    for term_data in terminals_data:
        # Check if terminal already exists
        existing = POSDevice.query.filter_by(terminal_code=term_data["terminal_code"]).first()
        if existing:
            print(f"   - Terminal {term_data['terminal_code']} already exists, skipping...")
            created_terminals.append(existing)
            continue
        
        terminal = POSDevice(
            name=term_data["name"],
            terminal_code=term_data["terminal_code"],
            location=term_data["location"],
            is_active=True,
        )
        db.session.add(terminal)
        created_terminals.append(terminal)
        print(f"   ✓ Created terminal: {term_data['name']} ({term_data['terminal_code']})")
    
    db.session.flush()
    return created_terminals


def create_pos_products():
    """Create POS products with categories."""
    print("\n2. Creating POS Products...")
    
    products_data = [
        # Food Items
        {"name": "Grilled Chicken", "category": "Food", "price": Decimal("15000.00"), "description": "Tender grilled chicken with spices"},
        {"name": "Beef Stew", "category": "Food", "price": Decimal("18000.00"), "description": "Traditional beef stew with vegetables"},
        {"name": "Fish & Chips", "category": "Food", "price": Decimal("20000.00"), "description": "Crispy fish fillet with chips"},
        {"name": "Rice & Beans", "category": "Food", "price": Decimal("8000.00"), "description": "Steamed rice with beans"},
        {"name": "Matooke & Groundnut Sauce", "category": "Food", "price": Decimal("12000.00"), "description": "Steamed matooke with groundnut sauce"},
        {"name": "Chapati", "category": "Food", "price": Decimal("3000.00"), "description": "Fresh made chapati"},
        {"name": "Rolex", "category": "Food", "price": Decimal("5000.00"), "description": "Chapati with eggs and vegetables"},
        {"name": "Pilau Rice", "category": "Food", "price": Decimal("10000.00"), "description": "Spiced pilau rice"},
        
        # Drinks
        {"name": "Soda (Coke)", "category": "Drinks", "price": Decimal("3000.00"), "description": "Coca-Cola 500ml"},
        {"name": "Soda (Fanta)", "category": "Drinks", "price": Decimal("3000.00"), "description": "Fanta Orange 500ml"},
        {"name": "Soda (Sprite)", "category": "Drinks", "price": Decimal("3000.00"), "description": "Sprite 500ml"},
        {"name": "Water (Bottle)", "category": "Drinks", "price": Decimal("2000.00"), "description": "Bottled water 500ml"},
        {"name": "Fresh Juice (Mango)", "category": "Drinks", "price": Decimal("5000.00"), "description": "Fresh mango juice"},
        {"name": "Fresh Juice (Pineapple)", "category": "Drinks", "price": Decimal("5000.00"), "description": "Fresh pineapple juice"},
        {"name": "Coffee (Black)", "category": "Drinks", "price": Decimal("4000.00"), "description": "Black coffee"},
        {"name": "Tea", "category": "Drinks", "price": Decimal("3000.00"), "description": "Hot tea"},
        
        # Snacks
        {"name": "Samosa", "category": "Snacks", "price": Decimal("2000.00"), "description": "Crispy samosa"},
        {"name": "Spring Roll", "category": "Snacks", "price": Decimal("2500.00"), "description": "Vegetable spring roll"},
        {"name": "Mandazi", "category": "Snacks", "price": Decimal("1500.00"), "description": "Sweet mandazi"},
        {"name": "Chips (French Fries)", "category": "Snacks", "price": Decimal("4000.00"), "description": "French fries"},
        
        # Desserts
        {"name": "Cake Slice", "category": "Desserts", "price": Decimal("8000.00"), "description": "Assorted cake slice"},
        {"name": "Ice Cream", "category": "Desserts", "price": Decimal("5000.00"), "description": "Vanilla ice cream"},
        {"name": "Fruit Salad", "category": "Desserts", "price": Decimal("6000.00"), "description": "Fresh mixed fruit salad"},
        
        # Services
        {"name": "Delivery Fee", "category": "Services", "price": Decimal("5000.00"), "description": "Delivery service charge"},
        {"name": "Packaging Fee", "category": "Services", "price": Decimal("2000.00"), "description": "Takeaway packaging"},
    ]
    
    created_products = []
    for prod_data in products_data:
        # Check if product already exists
        existing = POSProduct.query.filter_by(
            name=prod_data["name"],
            category=prod_data["category"]
        ).first()
        
        if existing:
            print(f"   - Product '{prod_data['name']}' already exists, skipping...")
            created_products.append(existing)
            continue
        
        product = POSProduct(
            name=prod_data["name"],
            category=prod_data["category"],
            price=prod_data["price"],
            description=prod_data["description"],
            is_available=True,
            is_active=True,
            tax_rate=Decimal("18.00"),
        )
        db.session.add(product)
        created_products.append(product)
        print(f"   ✓ Created product: {prod_data['name']} - {prod_data['category']} (UGX {prod_data['price']:,.0f})")
    
    db.session.flush()
    return created_products


def create_pos_sample_data(terminals, products, users):
    """Create sample orders, shifts, and payments."""
    print("\n3. Creating Sample Orders and Shifts...")
    
    if not terminals:
        print("   ⚠️  No terminals available, skipping sample orders...")
        return
    
    if not products:
        print("   ⚠️  No products available, skipping sample orders...")
        return
    
    if not users:
        print("   ⚠️  No users available, skipping sample orders...")
        return
    
    # Get or create walk-in client
    walk_in_client = Client.query.filter_by(name="Walk-in Customer").first()
    if not walk_in_client:
        walk_in_client = Client(
            name="Walk-in Customer",
            phone="000-000-0000",
            email="walkin@example.com",
        )
        db.session.add(walk_in_client)
        db.session.flush()
        print("   ✓ Created walk-in client")
    
    orders_created = 0
    shifts_created = 0
    
    # Create past shifts with orders (last 7 days)
    for day_offset in range(7, 0, -1):
        order_date = datetime.now() - timedelta(days=day_offset)
        
        for terminal in terminals[:2]:  # Use first 2 terminals
            user = random.choice(users)
            
            # Create a closed shift for this day
            shift = POSShift(
                device_id=terminal.id,
                user_id=user.id,
                starting_cash=Decimal("100000.00"),
                ending_cash=Decimal("350000.00"),
                status="closed",
                started_at=order_date.replace(hour=8, minute=0),
                ended_at=order_date.replace(hour=18, minute=0),
            )
            db.session.add(shift)
            db.session.flush()
            shifts_created += 1
            
            # Create 5-10 orders for this shift
            num_orders = random.randint(5, 10)
            for order_num in range(num_orders):
                order_time = order_date.replace(
                    hour=random.randint(9, 17),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                
                # Create order
                order = POSOrder(
                    device_id=terminal.id,
                    shift_id=shift.id,
                    client_id=walk_in_client.id if random.random() > 0.3 else None,
                    reference=generate_order_reference(),
                    order_time=order_time,
                    total_amount=Decimal("0.00"),
                    tax_amount=Decimal("0.00"),
                    discount_amount=Decimal("0.00"),
                    status="paid",
                    is_delivery=random.choice([True, False]),
                )
                db.session.add(order)
                db.session.flush()
                orders_created += 1
                
                # Add 2-5 items to order
                num_items = random.randint(2, 5)
                selected_products = random.sample(products, min(num_items, len(products)))
                subtotal = Decimal("0.00")
                
                for product in selected_products:
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
                        is_kitchen_item=(product.category == "Food"),
                    )
                    db.session.add(line)
                
                # Calculate tax (18%)
                tax_rate = Decimal("0.18")
                tax_amount = subtotal * tax_rate
                total_amount = subtotal + tax_amount
                
                order.total_amount = total_amount
                order.tax_amount = tax_amount
                
                # Create payment
                payment_method = random.choice(["cash", "card", "mobile_money"])
                payment = POSPayment(
                    order_id=order.id,
                    amount=total_amount,
                    method=payment_method,
                    reference=f"REF-{random.randint(100000, 999999)}" if payment_method != "cash" else None,
                )
                db.session.add(payment)
                db.session.flush()
                
                # Create receipt (80% of orders have receipts)
                if random.random() > 0.2:
                    receipt = POSReceipt(
                        payment_id=payment.id,
                        order_id=order.id,
                        receipt_ref=generate_order_reference("RCP"),
                        receipt_number=generate_order_reference("RCP"),
                    )
                    db.session.add(receipt)
    
    # Create today's open shift for first terminal
    print("\n4. Creating Today's Open Shift...")
    device = terminals[0]
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
            starting_cash=Decimal("50000.00"),
            status="open",
            started_at=datetime.now().replace(hour=8, minute=0),
        )
        db.session.add(today_shift)
        print("   ✓ Created open shift for today")
    else:
        print("   - Open shift already exists for today")
    
    print(f"\n   ✓ Created {shifts_created} closed shifts")
    print(f"   ✓ Created {orders_created} sample orders with payments")


def setup_pos_system():
    """Main function to set up complete POS system."""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("POS SYSTEM SETUP")
        print("=" * 70)
        print()
        
        try:
            # Check for existing data
            existing_terminals = POSDevice.query.count()
            existing_products = POSProduct.query.count()
            existing_orders = POSOrder.query.count()
            
            if existing_terminals > 0 or existing_products > 0 or existing_orders > 0:
                print("⚠️  Existing POS data found:")
                print(f"   - Terminals: {existing_terminals}")
                print(f"   - Products: {existing_products}")
                print(f"   - Orders: {existing_orders}")
                response = input("\nDo you want to continue and add more data? (yes/no): ")
                if response.lower() != 'yes':
                    print("Cancelled.")
                    return False
            
            # Get users
            users = User.query.limit(3).all()
            if not users:
                print("❌ No users found. Please create at least one user first.")
                return False
            
            print(f"Using {len(users)} user(s) for shifts and orders\n")
            
            # Create terminals
            terminals = create_pos_terminals()
            
            # Create products
            products = create_pos_products()
            
            # Create sample data
            create_pos_sample_data(terminals, products, users)
            
            # Commit everything
            print("\n" + "=" * 70)
            print("Committing all changes to database...")
            db.session.commit()
            
            print("\n" + "=" * 70)
            print("✅ POS SYSTEM SETUP COMPLETE!")
            print("=" * 70)
            print("\nCreated:")
            print(f"  ✓ {len(terminals)} POS Terminal(s)")
            print(f"  ✓ {len(products)} POS Product(s)")
            
            # Count what was created
            total_terminals = POSDevice.query.count()
            total_products = POSProduct.query.count()
            total_shifts = POSShift.query.count()
            total_orders = POSOrder.query.count()
            total_payments = POSPayment.query.count()
            
            print(f"\nCurrent POS System Status:")
            print(f"  - Total Terminals: {total_terminals}")
            print(f"  - Total Products: {total_products}")
            print(f"  - Total Shifts: {total_shifts}")
            print(f"  - Total Orders: {total_orders}")
            print(f"  - Total Payments: {total_payments}")
            
            print("\n" + "=" * 70)
            print("Next Steps:")
            print("  1. Go to POS System dashboard: /pos/")
            print("  2. View terminals: /pos/terminals")
            print("  3. Start a shift and create orders")
            print("=" * 70)
            print()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error setting up POS system: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = setup_pos_system()
    sys.exit(0 if success else 1)
