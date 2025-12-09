import os
import sys
from sqlalchemy import text

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import app
import app
from models import Role, db

app_instance = app.app

with app_instance.app_context():
    print("Dropping outdated roles table…")
    db.session.execute(text("DROP TABLE IF EXISTS roles"))
    db.session.commit()
    
    print("Recreating roles table…")
    db.create_all()
    
    print("Roles table repaired successfully.")

