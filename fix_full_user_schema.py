from app import create_app, db

from sqlalchemy import text


app = create_app()


with app.app_context():
    engine = db.engine


    print("\n🔍 Detecting database file...")
    print("DB URI:", app.config["SQLALCHEMY_DATABASE_URI"])


    # Check existing columns
    print("\n🔍 Checking existing user columns...")
    with engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(user)")).fetchall()
        col_names = [c[1] for c in cols]
        print("Existing columns:", col_names)


        # ADD role_id column if missing
        if "role_id" not in col_names:
            print("➡ Adding role_id column...")
            conn.execute(text("ALTER TABLE user ADD COLUMN role_id INTEGER"))
            conn.commit()
            print("✔ role_id added!")
        else:
            print("✔ role_id already exists")


        # ADD force_password_change column if missing
        if "force_password_change" not in col_names:
            print("➡ Adding force_password_change column...")
            conn.execute(text("ALTER TABLE user ADD COLUMN force_password_change BOOLEAN DEFAULT 0"))
            conn.commit()
            print("✔ force_password_change added!")
        else:
            print("✔ force_password_change already exists")


    # Ensure RBAC tables exist
    print("\n🔍 Ensuring RBAC tables exist...")
    db.create_all()
    print("✔ RBAC tables synced!")


    # Final schema output
    print("\n📌 FINAL USER TABLE STRUCTURE:")
    with engine.connect() as conn:
        cols = conn.execute(text("PRAGMA table_info(user)")).fetchall()
        for c in cols:
            print(" -", c[1])

