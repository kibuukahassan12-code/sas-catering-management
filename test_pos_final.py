"""Final test of POS system."""
from app import app

with app.app_context():
    with app.test_client() as client:
        try:
            from models import User, UserRole
            
            # Get admin user
            user = User.query.filter_by(role=UserRole.Admin).first()
            if not user:
                print("⚠ No admin user found")
                exit(1)
            
            # Simulate login
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            
            # Test POS route
            response = client.get('/pos/', follow_redirects=True)
            print(f"POS route status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ POS system working correctly!")
                print(f"Response length: {len(response.data)} bytes")
            else:
                print(f"✗ Error: Status {response.status_code}")
                if response.status_code == 500:
                    print("Response:", response.data[:1000].decode('utf-8', errors='ignore'))
            
        except Exception as e:
            import traceback
            print(f"✗ ERROR: {e}")
            print(traceback.format_exc())
