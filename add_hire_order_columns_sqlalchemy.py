"""Add missing columns to hire_order table using SQLAlchemy db.engine.execute()."""
import os
import sys

# Add sas_management to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sas_management_dir = os.path.join(current_dir, "sas_management")
sys.path.insert(0, current_dir)
sys.path.insert(0, sas_management_dir)

# Change to sas_management directory for imports
os.chdir(sas_management_dir)

from app import create_app
from sqlalchemy import text

app = create_app()

with app.app_context():
    from models import db
    
    print("=" * 60)
    print("Adding columns to hire_order table using db.engine.execute()")
    print("=" * 60)
    
    try:
        # Use SQLAlchemy 2.0 compatible syntax
        # For SQLAlchemy 2.0: use db.session.execute() or db.engine.connect()
        # For SQLAlchemy 1.x: use db.engine.execute()
        
        # Try SQLAlchemy 2.0 method first
        try:
            from sqlalchemy import __version__ as sa_version
            sa_major = int(sa_version.split('.')[0])
            
            if sa_major >= 2:
                # SQLAlchemy 2.0+ syntax
                with db.engine.connect() as conn:
                    print("\nExecuting: ALTER TABLE hire_order ADD COLUMN client_name TEXT;")
                    try:
                        conn.execute(text("ALTER TABLE hire_order ADD COLUMN client_name TEXT;"))
                        conn.commit()
                        print("[OK] Added column: client_name")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "duplicate column" in error_msg or "already exists" in error_msg:
                            print("[SKIP] Column client_name already exists")
                        else:
                            print(f"[ERROR] {e}")
                        conn.rollback()
                    
                    print("\nExecuting: ALTER TABLE hire_order ADD COLUMN telephone TEXT;")
                    try:
                        conn.execute(text("ALTER TABLE hire_order ADD COLUMN telephone TEXT;"))
                        conn.commit()
                        print("[OK] Added column: telephone")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "duplicate column" in error_msg or "already exists" in error_msg:
                            print("[SKIP] Column telephone already exists")
                        else:
                            print(f"[ERROR] {e}")
                        conn.rollback()
                    
                    print("\nExecuting: ALTER TABLE hire_order ADD COLUMN deposit_amount REAL;")
                    try:
                        conn.execute(text("ALTER TABLE hire_order ADD COLUMN deposit_amount REAL;"))
                        conn.commit()
                        print("[OK] Added column: deposit_amount")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "duplicate column" in error_msg or "already exists" in error_msg:
                            print("[SKIP] Column deposit_amount already exists")
                        else:
                            print(f"[ERROR] {e}")
                        conn.rollback()
            else:
                # SQLAlchemy 1.x syntax (legacy)
                print("\nExecuting: ALTER TABLE hire_order ADD COLUMN client_name TEXT;")
                try:
                    db.engine.execute(text("ALTER TABLE hire_order ADD COLUMN client_name TEXT;"))
                    print("[OK] Added column: client_name")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "duplicate column" in error_msg or "already exists" in error_msg:
                        print("[SKIP] Column client_name already exists")
                    else:
                        print(f"[ERROR] {e}")
                
                print("\nExecuting: ALTER TABLE hire_order ADD COLUMN telephone TEXT;")
                try:
                    db.engine.execute(text("ALTER TABLE hire_order ADD COLUMN telephone TEXT;"))
                    print("[OK] Added column: telephone")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "duplicate column" in error_msg or "already exists" in error_msg:
                        print("[SKIP] Column telephone already exists")
                    else:
                        print(f"[ERROR] {e}")
                
                print("\nExecuting: ALTER TABLE hire_order ADD COLUMN deposit_amount REAL;")
                try:
                    db.engine.execute(text("ALTER TABLE hire_order ADD COLUMN deposit_amount REAL;"))
                    print("[OK] Added column: deposit_amount")
                except Exception as e:
                    error_msg = str(e).lower()
                    if "duplicate column" in error_msg or "already exists" in error_msg:
                        print("[SKIP] Column deposit_amount already exists")
                    else:
                        print(f"[ERROR] {e}")
        except ImportError:
            # Fallback: use session.execute
            print("\nUsing db.session.execute() as fallback...")
            print("\nExecuting: ALTER TABLE hire_order ADD COLUMN client_name TEXT;")
            try:
                db.session.execute(text("ALTER TABLE hire_order ADD COLUMN client_name TEXT;"))
                db.session.commit()
                print("[OK] Added column: client_name")
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    print("[SKIP] Column client_name already exists")
                else:
                    print(f"[ERROR] {e}")
                db.session.rollback()
            
            print("\nExecuting: ALTER TABLE hire_order ADD COLUMN telephone TEXT;")
            try:
                db.session.execute(text("ALTER TABLE hire_order ADD COLUMN telephone TEXT;"))
                db.session.commit()
                print("[OK] Added column: telephone")
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    print("[SKIP] Column telephone already exists")
                else:
                    print(f"[ERROR] {e}")
                db.session.rollback()
            
            print("\nExecuting: ALTER TABLE hire_order ADD COLUMN deposit_amount REAL;")
            try:
                db.session.execute(text("ALTER TABLE hire_order ADD COLUMN deposit_amount REAL;"))
                db.session.commit()
                print("[OK] Added column: deposit_amount")
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate column" in error_msg or "already exists" in error_msg:
                    print("[SKIP] Column deposit_amount already exists")
                else:
                    print(f"[ERROR] {e}")
                db.session.rollback()
        
        print("\n" + "=" * 60)
        print("Migration completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
