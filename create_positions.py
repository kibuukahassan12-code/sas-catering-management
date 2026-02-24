#!/usr/bin/env python3
"""
Create Employee Positions and Update Employees
This script creates position records and links employees to them.
"""
import os
import sys
os.environ["SECRET_KEY"] = "sas-management-system-secret-key-2024-production"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import db, Position, Employee, Department

app = create_app()

def create_positions_and_update_employees():
    """Create positions and update employees."""
    with app.app_context():
        print("=" * 80)
        print("CREATING EMPLOYEE POSITIONS")
        print("=" * 80)
        print()
        
        # Create common positions with realistic names
        positions_data = [
            {"title": "Manager", "description": "General manager responsible for overall operations"},
            {"title": "Chef", "description": "Head chef responsible for kitchen operations"},
            {"title": "Cashier", "description": "Handles cash transactions and customer payments"},
            {"title": "Security Guard", "description": "Provides security and safety for premises"},
            {"title": "Waiter", "description": "Serves guests at events and restaurants"},
            {"title": "Kitchen Staff", "description": "Assists in kitchen operations and food preparation"},
            {"title": "Driver", "description": "Handles transportation and deliveries"},
            {"title": "Event Manager", "description": "Manages events and client relations"},
            {"title": "Accountant", "description": "Handles financial records and accounting"},
            {"title": "Sales Manager", "description": "Manages sales and client acquisition"},
            {"title": "Production Manager", "description": "Manages production operations"},
            {"title": "Inventory Manager", "description": "Manages inventory and supplies"},
            {"title": "Supervisor", "description": "Supervises daily operations and staff"},
            {"title": "Cook", "description": "Prepares food items"},
            {"title": "Bartender", "description": "Prepares and serves beverages"},
            {"title": "Cleaner", "description": "Maintains cleanliness of facilities"},
            {"title": "Receptionist", "description": "Handles front desk and customer inquiries"},
            {"title": "HR Manager", "description": "Manages human resources and employee relations"},
        ]
        
        positions_created = 0
        position_map = {}
        
        for pos_data in positions_data:
            position = Position.query.filter_by(title=pos_data["title"]).first()
            if not position:
                position = Position(
                    title=pos_data["title"],
                    description=pos_data["description"]
                )
                db.session.add(position)
                db.session.flush()
                positions_created += 1
                print(f"  [OK] Created position: {pos_data['title']}")
            else:
                print(f"  [OK] Position already exists: {pos_data['title']}")
            position_map[pos_data["title"].lower()] = position
        
        db.session.commit()
        print(f"\n[OK] Created {positions_created} positions (Total: {Position.query.count()})")
        
        # Update employees to use position_obj instead of legacy position field
        print("\n[STEP] Updating employees to use position objects...")
        employees_updated = 0
        
        # Map old position names to new realistic ones
        position_mapping = {
            "chef": "Chef",
            "cook": "Cook",
            "kitchen": "Kitchen Staff",
            "waiter": "Waiter",
            "server": "Waiter",
            "manager": "Manager",
            "event manager": "Event Manager",
            "event": "Event Manager",
            "driver": "Driver",
            "hr": "HR Manager",
            "human resources": "HR Manager",
            "accountant": "Accountant",
            "accounting": "Accountant",
            "sales": "Sales Manager",
            "production": "Production Manager",
            "inventory": "Inventory Manager",
            "cashier": "Cashier",
            "security": "Security Guard",
            "guard": "Security Guard",
            "supervisor": "Supervisor",
            "bartender": "Bartender",
            "cleaner": "Cleaner",
            "receptionist": "Receptionist",
        }
        
        employees = Employee.query.all()
        for employee in employees:
            # If employee has legacy position string but no position_obj, link them
            if employee.position and not employee.position_obj:
                position_title = employee.position.strip()
                matching_position = None
                
                # Try exact match first
                matching_position = Position.query.filter_by(title=position_title).first()
                
                # Try case-insensitive match
                if not matching_position:
                    matching_position = Position.query.filter(
                        db.func.lower(Position.title) == position_title.lower()
                    ).first()
                
                # Try mapping from old names to new names
                if not matching_position:
                    position_lower = position_title.lower()
                    for old_name, new_name in position_mapping.items():
                        if old_name in position_lower:
                            matching_position = Position.query.filter_by(title=new_name).first()
                            if matching_position:
                                break
                
                # Try partial match with position_map
                if not matching_position:
                    for pos_title, pos_obj in position_map.items():
                        if pos_title in position_title.lower() or position_title.lower() in pos_title:
                            matching_position = pos_obj
                            break
                
                if matching_position:
                    employee.position_obj = matching_position
                    employee.position_id = matching_position.id
                    employees_updated += 1
                    print(f"  [OK] Updated {employee.full_name}: '{employee.position}' -> '{matching_position.title}'")
                else:
                    # Create a new position if no match found
                    new_position = Position(title=position_title)
                    db.session.add(new_position)
                    db.session.flush()
                    employee.position_obj = new_position
                    employee.position_id = new_position.id
                    employees_updated += 1
                    print(f"  [OK] Created new position '{position_title}' for {employee.full_name}")
            # If employee has no position at all, assign a default one
            elif not employee.position and not employee.position_obj:
                default_position = Position.query.filter_by(title="Manager").first()
                if not default_position:
                    default_position = Position.query.filter_by(title="Supervisor").first()
                if not default_position:
                    default_position = Position(title="Manager", description="General manager position")
                    db.session.add(default_position)
                    db.session.flush()
                employee.position_obj = default_position
                employee.position_id = default_position.id
                employees_updated += 1
                print(f"  [OK] Assigned default position '{default_position.title}' to {employee.full_name}")
        
        db.session.commit()
        print(f"\n[OK] Updated {employees_updated} employees")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Positions: {Position.query.count()}")
        print(f"Total Employees: {Employee.query.count()}")
        employees_with_positions = Employee.query.filter(Employee.position_obj != None).count()
        print(f"Employees with Position Objects: {employees_with_positions}")
        print("=" * 80)
        print()

if __name__ == "__main__":
    create_positions_and_update_employees()
