"""Test POS product creation and availability."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sas_management.app import create_app
from sas_management.models import db, POSProduct
from decimal import Decimal

app = create_app()

with app.app_context():
    print("Testing POS Product Model...")
    print("=" * 60)
    
    # Check if is_active field exists
    if hasattr(POSProduct, 'is_active'):
        print("[OK] POSProduct has 'is_active' field")
    else:
        print("[ERROR] POSProduct missing 'is_active' field")
    
    # Check if is_available field exists
    if hasattr(POSProduct, 'is_available'):
        print("[OK] POSProduct has 'is_available' field")
    else:
        print("[ERROR] POSProduct missing 'is_available' field")
    
    # Count products
    total = POSProduct.query.count()
    available = POSProduct.query.filter_by(is_available=True).count()
    active = POSProduct.query.filter_by(is_active=True).count() if hasattr(POSProduct, 'is_active') else 0
    
    print(f"\nTotal POS Products: {total}")
    print(f"Available Products: {available}")
    print(f"Active Products: {active}")
    
    # Try to create a test product
    print("\nTesting product creation...")
    try:
        test_product = POSProduct(
            name="Test Product",
            category="Test",
            price=Decimal("1000.00"),
            is_available=True,
            is_active=True,
        )
        db.session.add(test_product)
        db.session.commit()
        print("[OK] Test product created successfully")
        
        # Delete test product
        db.session.delete(test_product)
        db.session.commit()
        print("[OK] Test product deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Failed to create test product: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test complete!")

