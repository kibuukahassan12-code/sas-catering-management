"""Test script to verify app.py runs correctly."""
try:
    from app import create_app
    app = create_app()
    print("✓ App created successfully")
    print("✓ All imports working")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

