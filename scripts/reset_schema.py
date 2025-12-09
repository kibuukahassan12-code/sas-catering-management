import os
import sys
from sqlalchemy import text

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import app
import app
from models import db

app_instance = app.app

with app_instance.app_context():
    print("Dropping outdated tables...")
    db.session.execute(text("DROP TABLE IF EXISTS menu_package"))
    db.session.execute(text("DROP TABLE IF EXISTS event"))
    db.session.commit()
    print("Recreating all tables from models...")
    db.create_all()
    print("Schema repair completed successfully.")

