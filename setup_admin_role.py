from app import create_app
from models import User, Role, Permission, db

app = create_app()

with app.app_context():
    admin_role = Role.query.filter_by(name="Admin").first()
    if not admin_role:
        admin_role = Role(name="Admin", description="System Super Administrator")
        db.session.add(admin_role)
        db.session.commit()

    user = User.query.get(1)
    if user:
        user.role_id = admin_role.id
        db.session.commit()
        print("Admin role assigned to User ID 1")
    else:
        print("User ID 1 not found")

