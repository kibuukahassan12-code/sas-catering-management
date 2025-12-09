"""Seed Premium Modules with sample data."""
from app import create_app
from models import (
    db, FloorPlan, SeatingAssignment, MenuCategory, MenuItem, MenuPackage, MenuPackageItem,
    Contract, ContractTemplate, Event, Client, User
)
from datetime import datetime, date

def seed_premium_modules():
    """Seed premium modules sample data."""
    app = create_app()
    
    with app.app_context():
        try:
            print("Seeding Premium Modules sample data...")
            
            # Get admin user
            admin_user = User.query.filter_by(role='Admin').first()
            if not admin_user:
                print("  ⚠️  No admin user found - skipping seed")
                return
            
            # 1. Create Menu Category
            existing_category = MenuCategory.query.filter_by(name="Catering Classics").first()
            if not existing_category:
                category = MenuCategory(name="Catering Classics", description="Traditional catering favorites")
                db.session.add(category)
                db.session.flush()
                print("    ✓ Menu category created")
            else:
                category = existing_category
                print("    ✓ Menu category already exists")
            
            # 2. Create Menu Item
            existing_item = MenuItem.query.filter_by(name="Grilled Chicken").first()
            if not existing_item:
                menu_item = MenuItem(
                    name="Grilled Chicken",
                    category_id=category.id,
                    description="Succulent grilled chicken breast with herbs",
                    cost_per_portion=4500.00,
                    selling_price=8000.00,
                    margin_percent=((8000 - 4500) / 8000 * 100),
                    status="Active"
                )
                db.session.add(menu_item)
                db.session.flush()
                print("    ✓ Menu item created (margin: {:.1f}%)".format(menu_item.margin_percent))
            else:
                menu_item = existing_item
                print("    ✓ Menu item already exists")
            
            # 3. Create Menu Package
            existing_package = MenuPackage.query.filter_by(name="Wedding Gold Package").first()
            if not existing_package:
                package = MenuPackage(
                    name="Wedding Gold Package",
                    category="Wedding",
                    description="Complete wedding catering package with appetizers, main course, and dessert",
                    total_price=50000.00,
                    status="Active"
                )
                db.session.add(package)
                db.session.flush()
                
                # Add item to package
                package_item = MenuPackageItem(
                    package_id=package.id,
                    menu_item_id=menu_item.id,
                    quantity=1
                )
                db.session.add(package_item)
                
                # Recalculate totals
                package.total_cost = menu_item.cost_per_portion * 1
                package.margin_percent = ((package.total_price - package.total_cost) / package.total_price * 100)
                
                print("    ✓ Menu package created")
            else:
                print("    ✓ Menu package already exists")
            
            # 4. Create Sample Floor Plan
            first_event = Event.query.first()
            if first_event:
                existing_plan = FloorPlan.query.filter_by(event_id=first_event.id).first()
                if not existing_plan:
                    floorplan = FloorPlan(
                        event_id=first_event.id,
                        name=f"Floor Plan - {first_event.event_name}",
                        json_layout='{"version":"4.5.0","objects":[]}',
                        created_by=admin_user.id
                    )
                    db.session.add(floorplan)
                    print(f"    ✓ Floor plan created for event #{first_event.id}")
                else:
                    print(f"    ✓ Floor plan already exists for event #{first_event.id}")
            
            # 5. Create Contract Template
            existing_template = ContractTemplate.query.filter_by(name="Standard Event Contract").first()
            if not existing_template:
                template_body = """<h1>Event Contract Agreement</h1>
                <p>This contract is entered into between SAS Best Foods and <strong>{client_name}</strong>.</p>
                <h2>Event Details</h2>
                <ul>
                    <li><strong>Event Name:</strong> {event_name}</li>
                    <li><strong>Event Date:</strong> {event_date}</li>
                    <li><strong>Event Time:</strong> {event_time}</li>
                    <li><strong>Venue:</strong> {venue}</li>
                    <li><strong>Expected Guests:</strong> {guest_count}</li>
                </ul>
                <h2>Package</h2>
                <p>Package: {package_name}</p>
                <h2>Terms and Conditions</h2>
                <p>All catering services will be provided according to the agreed specifications. Payment terms and cancellation policies apply as per our standard terms.</p>
                <p><strong>Contract Date:</strong> {today}</p>
                <p>By signing below, both parties agree to the terms and conditions outlined in this contract.</p>
                <p>_________________________</p>
                <p>SAS Best Foods</p>
                <p>_________________________</p>
                <p>Client Signature</p>"""
                
                template = ContractTemplate(
                    name="Standard Event Contract",
                    body=template_body,
                    description="Standard contract template with all common placeholders",
                    is_default=True
                )
                db.session.add(template)
                print("    ✓ Contract template created")
            else:
                print("    ✓ Contract template already exists")
            
            db.session.commit()
            print("\n✅ Premium Modules sample data seeded successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error seeding premium modules: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    seed_premium_modules()

