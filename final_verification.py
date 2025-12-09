"""Final verification - test all critical queries that were failing."""
from app import app, db
from models import InventoryItem, IncomingLead, User, Client, Event, Task
from datetime import date

print("=" * 70)
print("FINAL SYSTEM VERIFICATION")
print("=" * 70)
print()

with app.app_context():
    all_passed = True
    errors = []
    
    # Test 1: InventoryItem (was failing - missing unit_price_ugx)
    try:
        count = InventoryItem.query.filter(InventoryItem.stock_count <= 10).count()
        print(f"✓ Test 1: InventoryItem low stock query - {count} items")
    except Exception as e:
        print(f"✗ Test 1: InventoryItem query FAILED - {e}")
        all_passed = False
        errors.append(("InventoryItem", str(e)))
    
    # Test 2: IncomingLead (was failing - missing email)
    try:
        count = IncomingLead.query.filter_by(pipeline_stage='New Lead').count()
        print(f"✓ Test 2: IncomingLead pipeline query - {count} leads")
    except Exception as e:
        print(f"✗ Test 2: IncomingLead query FAILED - {e}")
        all_passed = False
        errors.append(("IncomingLead", str(e)))
    
    # Test 3: Task (was failing - missing created_at)
    try:
        count = Task.query.filter(Task.due_date <= date.today()).filter(Task.status != 'Complete').count()
        print(f"✓ Test 3: Task overdue query - {count} tasks")
    except Exception as e:
        print(f"✗ Test 3: Task query FAILED - {e}")
        all_passed = False
        errors.append(("Task", str(e)))
    
    # Test 4: User
    try:
        count = User.query.count()
        print(f"✓ Test 4: User query - {count} users")
    except Exception as e:
        print(f"✗ Test 4: User query FAILED - {e}")
        all_passed = False
        errors.append(("User", str(e)))
    
    # Test 5: Client
    try:
        count = Client.query.filter(Client.is_archived == False).count()
        print(f"✓ Test 5: Client query - {count} active clients")
    except Exception as e:
        print(f"✗ Test 5: Client query FAILED - {e}")
        all_passed = False
        errors.append(("Client", str(e)))
    
    # Test 6: Event
    try:
        count = Event.query.count()
        print(f"✓ Test 6: Event query - {count} events")
    except Exception as e:
        print(f"✗ Test 6: Event query FAILED - {e}")
        all_passed = False
        errors.append(("Event", str(e)))
    
    print()
    print("=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED - SYSTEM IS FULLY OPERATIONAL!")
    else:
        print("✗ SOME TESTS FAILED:")
        for model, error in errors:
            print(f"   - {model}: {error}")
        print()
        print("   Run: python scan_all_models_for_missing_columns.py")
    print("=" * 70)
    print()
    print("⚠️  Remember to restart your Flask application!")

