"""Test POS system after fixes."""
from app import app

with app.app_context():
    try:
        print("Testing POS system...")
        
        # Test imports
        from blueprints.pos import pos_bp
        from models import POSDevice, POSShift
        print("✓ All imports successful")
        
        # Test queries
        devices = POSDevice.query.filter_by(is_active=True).all()
        print(f"✓ Devices query: {len(devices)} devices found")
        
        shifts = POSShift.query.filter_by(status="open").all()
        print(f"✓ Shifts query: {len(shifts)} open shifts found")
        
        # Test route with test client
        with app.test_client() as client:
            from models import User, UserRole
            user = User.query.filter_by(role=UserRole.Admin).first()
            
            if user:
                # Simulate login
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(user.id)
                    sess['_fresh'] = True
                
                # Test POS index route
                response = client.get('/pos/', follow_redirects=True)
                print(f"✓ POS route status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✓ POS route working correctly!")
                else:
                    print(f"⚠ Unexpected status: {response.status_code}")
                    if response.status_code == 500:
                        print("Response data:", response.data[:500])
            else:
                print("⚠ No admin user found for testing")
        
    except Exception as e:
        import traceback
        print(f"✗ ERROR: {e}")
        print(traceback.format_exc())

