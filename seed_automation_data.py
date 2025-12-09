#!/usr/bin/env python3
"""
Seed Automation Sample Data
Creates sample workflows and action logs for testing.
"""

import sys
import os
from datetime import datetime, timedelta
import json
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import (
    Workflow,
    ActionLog,
    User,
    Event,
    UserRole
)

def seed_automation_data():
    """Seed automation sample data."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("AUTOMATION SAMPLE DATA SEEDING")
        print("=" * 60)
        print()
        
        # Get admin user
        admin_user = User.query.filter_by(role=UserRole.Admin).first()
        if not admin_user:
            users = User.query.limit(1).all()
            if not users:
                print("⚠️  No users found. Please create users first.")
                return False
        
        # Sample workflows
        workflows_data = [
            {
                "name": "Auto-Send Event Confirmation",
                "description": "Automatically sends confirmation email when event status changes to 'Confirmed'",
                "trigger_type": "event_status_change",
                "trigger_config": json.dumps({
                    "status": "Confirmed",
                    "send_email": True,
                    "send_sms": False
                }),
                "actions": json.dumps([
                    {
                        "type": "send_email",
                        "template": "event_confirmation",
                        "recipients": ["client_email", "sales_manager"]
                    },
                    {
                        "type": "create_task",
                        "title": "Prepare event materials",
                        "assign_to": "event_coordinator"
                    }
                ]),
                "is_active": True
            },
            {
                "name": "Low Stock Alert",
                "description": "Sends alert when inventory items fall below threshold",
                "trigger_type": "inventory_low_stock",
                "trigger_config": json.dumps({
                    "threshold": 10,
                    "alert_frequency": "daily"
                }),
                "actions": json.dumps([
                    {
                        "type": "send_notification",
                        "channels": ["email", "dashboard"],
                        "recipients": ["inventory_manager", "admin"]
                    },
                    {
                        "type": "create_task",
                        "title": "Restock inventory item",
                        "priority": "high"
                    }
                ]),
                "is_active": True
            },
            {
                "name": "Invoice Reminder",
                "description": "Sends reminder emails for overdue invoices",
                "trigger_type": "invoice_overdue",
                "trigger_config": json.dumps({
                    "days_overdue": 7,
                    "reminder_frequency": "weekly"
                }),
                "actions": json.dumps([
                    {
                        "type": "send_email",
                        "template": "invoice_reminder",
                        "recipients": ["client_email"]
                    },
                    {
                        "type": "update_invoice",
                        "add_reminder_note": True
                    }
                ]),
                "is_active": True
            },
            {
                "name": "Event Day Checklist",
                "description": "Creates checklist items 3 days before event",
                "trigger_type": "event_date_approaching",
                "trigger_config": json.dumps({
                    "days_before": 3,
                    "checklist_template": "standard_event"
                }),
                "actions": json.dumps([
                    {
                        "type": "create_checklist",
                        "template": "event_preparation",
                        "assign_to": "event_manager"
                    },
                    {
                        "type": "send_notification",
                        "message": "Event checklist created",
                        "recipients": ["event_manager"]
                    }
                ]),
                "is_active": True
            },
            {
                "name": "New Lead Assignment",
                "description": "Automatically assigns new leads to available sales manager",
                "trigger_type": "new_lead_created",
                "trigger_config": json.dumps({
                    "assignment_rule": "round_robin",
                    "priority": "high"
                }),
                "actions": json.dumps([
                    {
                        "type": "assign_lead",
                        "method": "round_robin",
                        "role": "SalesManager"
                    },
                    {
                        "type": "send_notification",
                        "message": "New lead assigned",
                        "recipients": ["assigned_user"]
                    }
                ]),
                "is_active": True
            },
            {
                "name": "Payment Received Notification",
                "description": "Notifies team when payment is received",
                "trigger_type": "payment_received",
                "trigger_config": json.dumps({
                    "min_amount": 0,
                    "notify_channels": ["email", "dashboard"]
                }),
                "actions": json.dumps([
                    {
                        "type": "send_notification",
                        "channels": ["email", "dashboard"],
                        "recipients": ["accounting_manager", "sales_manager"]
                    },
                    {
                        "type": "update_invoice_status",
                        "status": "paid"
                    }
                ]),
                "is_active": True
            },
            {
                "name": "Temperature Alert",
                "description": "Alerts when temperature readings are outside safe range",
                "trigger_type": "temperature_violation",
                "trigger_config": json.dumps({
                    "min_temp": 0,
                    "max_temp": 10,
                    "alert_immediately": True
                }),
                "actions": json.dumps([
                    {
                        "type": "send_alert",
                        "priority": "critical",
                        "recipients": ["kitchen_manager", "admin"]
                    },
                    {
                        "type": "create_incident",
                        "type": "temperature_violation",
                        "severity": "high"
                    }
                ]),
                "is_active": True
            },
            {
                "name": "Weekly Sales Report",
                "description": "Generates and emails weekly sales report every Monday",
                "trigger_type": "scheduled",
                "trigger_config": json.dumps({
                    "schedule": "weekly",
                    "day": "monday",
                    "time": "09:00"
                }),
                "actions": json.dumps([
                    {
                        "type": "generate_report",
                        "report_type": "weekly_sales",
                        "format": "pdf"
                    },
                    {
                        "type": "send_email",
                        "recipients": ["management_team"],
                        "attach_report": True
                    }
                ]),
                "is_active": True
            }
        ]
        
        # Create workflows
        print("1. Creating Workflows...")
        workflows_created = 0
        
        for wf_data in workflows_data:
            existing = Workflow.query.filter_by(name=wf_data["name"]).first()
            if not existing:
                workflow = Workflow(
                    name=wf_data["name"],
                    description=wf_data["description"],
                    trigger_type=wf_data["trigger_type"],
                    trigger_config=wf_data["trigger_config"],
                    actions=wf_data["actions"],
                    is_active=wf_data["is_active"],
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
                )
                db.session.add(workflow)
                workflows_created += 1
            else:
                workflow = existing
        
        db.session.commit()
        print(f"   ✓ Created {workflows_created} workflows")
        
        # Get all workflows for action logs
        all_workflows = Workflow.query.all()
        if not all_workflows:
            print("⚠️  No workflows available for action logs.")
            return False
        
        # Create action logs (last 30 days)
        print("\n2. Creating Action Logs...")
        action_types = [
            "send_email",
            "send_notification",
            "create_task",
            "create_checklist",
            "assign_lead",
            "update_invoice_status",
            "send_alert",
            "create_incident",
            "generate_report"
        ]
        
        statuses = ["success", "failed", "pending"]
        status_weights = [0.85, 0.10, 0.05]  # Most are successful
        
        logs_created = 0
        
        for i in range(100):  # Create 100 action logs
            days_ago = random.randint(0, 30)
            run_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            workflow = random.choice(all_workflows)
            action_type = random.choice(action_types)
            status = random.choices(statuses, weights=status_weights)[0]
            
            # Generate result based on status
            if status == "success":
                result = json.dumps({
                    "message": f"Action '{action_type}' executed successfully",
                    "recipients": random.randint(1, 5),
                    "execution_time_ms": random.randint(50, 500)
                })
            elif status == "failed":
                result = json.dumps({
                    "error": f"Failed to execute '{action_type}'",
                    "reason": random.choice([
                        "Network timeout",
                        "Invalid recipient",
                        "Template not found",
                        "Permission denied",
                        "Service unavailable"
                    ])
                })
            else:
                result = json.dumps({
                    "message": f"Action '{action_type}' is pending execution",
                    "queued_at": run_at.isoformat()
                })
            
            log = ActionLog(
                workflow_id=workflow.id,
                action_type=action_type,
                status=status,
                result=result,
                run_at=run_at
            )
            db.session.add(log)
            logs_created += 1
        
        db.session.commit()
        print(f"   ✓ Created {logs_created} action logs")
        
        print("\n" + "=" * 60)
        print("✅ AUTOMATION SAMPLE DATA SEEDING COMPLETE")
        print("=" * 60)
        print(f"\nCreated:")
        print(f"  - {workflows_created} workflows")
        print(f"  - {logs_created} action logs")
        print("\nYou can now view the data at:")
        print("  - /automation/")
        print()
        
        return True

if __name__ == "__main__":
    success = seed_automation_data()
    sys.exit(0 if success else 1)

