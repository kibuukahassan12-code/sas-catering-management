from app import create_app, db

from models import Permission


DEFAULT_PERMISSIONS = [
    ("view_dashboard", "Access dashboard"),
    ("manage_users", "Add/update/delete users"),
    ("assign_roles", "Assign roles and permissions"),
    ("view_orders", "View catering and hire orders"),
    ("manage_orders", "Create/update/delete orders"),
    ("view_inventory", "Access inventory module"),
    ("manage_inventory", "Modify inventory items"),
    ("view_finance", "Access finance module"),
    ("manage_finance", "Modify finance records"),
]

app = create_app()

with app.app_context():
    for code, desc in DEFAULT_PERMISSIONS:
        if not Permission.query.filter_by(code=code).first():
            db.session.add(Permission(code=code, description=desc))
    db.session.commit()
    print("Permissions created successfully.")

