"""Test POS system for errors."""
from app import app

with app.app_context():
    try:
        print("Testing POS imports...")
        from blueprints.pos import pos_bp
        print("✓ POS blueprint imported")
        
        from models import POSDevice, POSShift, POSOrder
        print("✓ POS models imported")
        
        from services.pos_service import create_order
        print("✓ POS service imported")
        
        print("\nTesting database queries...")
        devices = POSDevice.query.all()
        print(f"✓ POSDevice query works: {len(devices)} devices")
        
        shifts = POSShift.query.all()
        print(f"✓ POSShift query works: {len(shifts)} shifts")
        
        print("\nTesting route...")
        with app.test_client() as client:
            # Simulate login
            from models import User, UserRole
            user = User.query.filter_by(role=UserRole.Admin).first()
            if user:
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(user.id)
                    sess['_fresh'] = True
                
                response = client.get('/pos/')
                print(f"✓ POS route status: {response.status_code}")
                if response.status_code != 200:
                    print(f"Response: {response.data[:500]}")
            else:
                print("⚠ No admin user found for testing")
        
    except Exception as e:
        import traceback
        print(f"✗ ERROR: {e}")
        print(traceback.format_exc())

