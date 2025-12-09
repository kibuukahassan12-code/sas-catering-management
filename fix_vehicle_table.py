from app import app, db

from sqlalchemy import inspect, text



with app.app_context():

    try:

        inspector = inspect(db.engine)

        # Check if table exists

        if "vehicle" not in inspector.get_table_names():

            print("⚠️  Vehicle table does not exist. Creating it...")

            db.create_all()

            print("✓ Vehicle table created!")

            columns = []

        else:

            columns = [col["name"] for col in inspector.get_columns("vehicle")]



        fixes = []



        if "created_at" not in columns:

            fixes.append("ADD COLUMN created_at TEXT")



        if "updated_at" not in columns:

            fixes.append("ADD COLUMN updated_at TEXT")



        if "registration_number" not in columns:

            fixes.append("ADD COLUMN registration_number TEXT")



        if "make" not in columns:

            fixes.append("ADD COLUMN make TEXT")



        if "model" not in columns:

            fixes.append("ADD COLUMN model TEXT")



        if "capacity" not in columns:

            fixes.append("ADD COLUMN capacity INTEGER")



        if "is_active" not in columns:

            fixes.append("ADD COLUMN is_active INTEGER DEFAULT 1")



        if fixes:

            for fix in fixes:

                try:

                    # Use modern SQLAlchemy syntax

                    db.session.execute(text(f"ALTER TABLE vehicle {fix}"))

                    db.session.commit()

                except Exception as e:

                    print(f"⚠️  Error applying fix '{fix}': {e}")

                    db.session.rollback()

            print("✓ Vehicle table updated with missing columns:", fixes)

        else:

            print("✓ Vehicle table OK — no fixes needed!")

    except Exception as e:

        print(f"❌ Error: {e}")

        import traceback

        traceback.print_exc()

