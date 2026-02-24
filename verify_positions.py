#!/usr/bin/env python3
"""Verify positions and employee assignments."""
import os
import sys
os.environ["SECRET_KEY"] = "sas-management-system-secret-key-2024-production"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import db, Position, Employee

app = create_app()

with app.app_context():
    print("=" * 80)
    print("POSITION VERIFICATION")
    print("=" * 80)
    print()
    
    print("=== ALL AVAILABLE POSITIONS ===")
    positions = Position.query.order_by(Position.title).all()
    for i, p in enumerate(positions, 1):
        print(f"  {i:2d}. {p.title}")
    print(f"\nTotal: {len(positions)} positions")
    
    print("\n=== EMPLOYEE POSITION ASSIGNMENTS ===")
    employees = Employee.query.all()
    for e in employees:
        pos_title = e.position_obj.title if e.position_obj else "No Position"
        print(f"  {e.full_name}: {pos_title}")
    
    print("\n" + "=" * 80)
