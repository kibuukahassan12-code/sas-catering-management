"""Mobile Staff service."""
from flask import current_app

def get_staff_dashboard_data(user_id):
    """Get dashboard data for mobile staff."""
    try:
        from sas_management.models import Task, StaffTask
        tasks = Task.query.filter_by(assigned_to=user_id).filter_by(status='Pending').limit(10).all()
        staff_tasks = StaffTask.query.filter_by(assigned_to=user_id).filter_by(status='pending').limit(10).all()
        return {'success': True, 'tasks': tasks, 'staff_tasks': staff_tasks}
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error getting staff dashboard: {e}")
        return {'success': False, 'error': str(e)}

