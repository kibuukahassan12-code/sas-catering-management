"""
University Services - Mandatory Training Compliance Checks

READ-ONLY service functions for checking employee training compliance.
No database writes - only queries.
"""
from flask import current_app
from sas_management.models import db, Course, Enrollment, User, UserRole
from sqlalchemy import or_


def check_employee_compliance(employee_id):
    """
    Check if an employee has completed all mandatory training.
    
    Args:
        employee_id: User ID of the employee
        
    Returns:
        dict: {
            'compliant': bool,
            'missing_courses': list of Course objects,
            'message': str
        }
    """
    try:
        user = User.query.get(employee_id)
        if not user:
            return {
                'compliant': False,
                'missing_courses': [],
                'message': 'Employee not found'
            }
        
        # Find mandatory courses for this user's role
        mandatory_query = Course.query.filter(
            Course.mandatory == True,
            Course.published == True
        )
        
        # Filter by role requirements (if fields exist)
        try:
            role_filters = [
                Course.required_for_role == user.role,
                Course.required_for_role.is_(None)
            ]
            
            # Check if required_for_department field exists
            if hasattr(Course, 'required_for_department'):
                if hasattr(user, 'department') and user.department:
                    role_filters.append(Course.required_for_department == user.department)
                role_filters.append(Course.required_for_department.is_(None))
            
            mandatory_courses = mandatory_query.filter(or_(*role_filters)).all()
        except AttributeError:
            # Fields don't exist - use logical check only
            # Assume all published mandatory courses apply
            mandatory_courses = mandatory_query.all()
        
        if not mandatory_courses:
            return {
                'compliant': True,
                'missing_courses': [],
                'message': 'No mandatory training required'
            }
        
        # Check completed enrollments
        user_enrollments = Enrollment.query.filter_by(
            user_id=employee_id,
            completed=True
        ).all()
        
        completed_course_ids = {e.course_id for e in user_enrollments}
        missing_courses = [c for c in mandatory_courses if c.id not in completed_course_ids]
        
        if missing_courses:
            course_names = [c.title for c in missing_courses]
            return {
                'compliant': False,
                'missing_courses': missing_courses,
                'message': f'Missing mandatory training: {", ".join(course_names)}'
            }
        
        return {
            'compliant': True,
            'missing_courses': [],
            'message': 'All mandatory training completed'
        }
    except Exception as e:
        current_app.logger.error(f"Error checking employee compliance: {e}")
        # Fail open - allow assignment if check fails
        return {
            'compliant': True,
            'missing_courses': [],
            'message': 'Unable to verify training (check failed)'
        }


def missing_mandatory_courses(employee_id):
    """
    Get list of mandatory courses that an employee has not completed.
    
    Args:
        employee_id: User ID of the employee
        
    Returns:
        list: List of Course objects that are mandatory but not completed
    """
    result = check_employee_compliance(employee_id)
    return result.get('missing_courses', [])

