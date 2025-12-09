#!/usr/bin/env python3
"""
Create all missing database tables
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db, create_app
from models import HygieneReport

app = create_app()

with app.app_context():
    db.create_all()
    print("All missing tables created.")
