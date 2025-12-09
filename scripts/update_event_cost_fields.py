from app import app, db
from sqlalchemy import text

with app.app_context():
    fields = [
        "labor_cost FLOAT DEFAULT 0",
        "transport_cost FLOAT DEFAULT 0",
        "equipment_cost FLOAT DEFAULT 0",
        "ingredients_cost FLOAT DEFAULT 0",
        "total_cost FLOAT DEFAULT 0",
        "quoted_value FLOAT DEFAULT 0",
        "profit FLOAT DEFAULT 0"
    ]

    for field in fields:
        try:
            db.session.execute(text(f"ALTER TABLE event ADD COLUMN {field}"))
            print("Added:", field)
        except Exception:
            print("Already exists:", field)

    db.session.commit()
    print("Event costing columns updated successfully.")
