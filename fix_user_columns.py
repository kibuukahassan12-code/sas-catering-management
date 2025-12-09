from app import create_app, db

from sqlalchemy import inspect



app = create_app()



with app.app_context():

    inspector = inspect(db.engine)



    columns = [col["name"] for col in inspector.get_columns("user")]



    with db.engine.connect() as conn:

        if "role_id" not in columns:

            conn.execute(db.text("ALTER TABLE user ADD COLUMN role_id INTEGER"))

            print("✔ Added missing column: role_id")

        else:

            print("✔ role_id already exists")



        if "force_password_change" not in columns:

            conn.execute(db.text("ALTER TABLE user ADD COLUMN force_password_change BOOLEAN DEFAULT 0"))

            print("✔ Added missing column: force_password_change")

        else:

            print("✔ force_password_change already exists")
