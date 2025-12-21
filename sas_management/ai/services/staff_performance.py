"""
Staff Performance AI Service

Analyzes staff performance, attendance, and provides recommendations.
"""
from flask import current_app
from datetime import date, timedelta
from statistics import mean


def run(payload, user):
    """
    Run Staff Performance AI service.
    
    Args:
        payload: dict with 'staff_id' (optional) or 'department' (optional)
        user: Current user object
    
    Returns:
        dict: {
            'success': bool,
            'performance_score': float,
            'attendance_summary': dict,
            'recommendation': str,
            'error': str (if failed)
        }
    """
    try:
        from sas_management.models import Employee, Attendance
        
        staff_id = payload.get('staff_id')
        department = payload.get('department')
        
        if staff_id:
            # Single staff member analysis
            employee = Employee.query.get(staff_id)
            if not employee:
                return {
                    'success': False,
                    'error': f'Employee with ID {staff_id} not found',
                    'performance_score': 0.0,
                    'attendance_summary': {},
                    'recommendation': ''
                }
            
            return _analyze_employee(employee)
        
        elif department:
            # Department analysis
            employees = Employee.query.filter_by(department_id=department, is_active=True).all()
            if not employees:
                return {
                    'success': False,
                    'error': f'No employees found in department {department}',
                    'performance_score': 0.0,
                    'attendance_summary': {},
                    'recommendation': ''
                }
            
            return _analyze_department(employees)
        
        else:
            # Overall analysis
            all_employees = Employee.query.filter_by(is_active=True).all()
            return _analyze_department(all_employees, label='All Staff')
        
    except Exception as e:
        current_app.logger.exception(f"Staff Performance AI error: {e}")
        return {
            'success': False,
            'error': str(e),
            'performance_score': 0.0,
            'attendance_summary': {},
            'recommendation': ''
        }


def _analyze_employee(employee):
    """Analyze single employee performance."""
    # Get attendance data (last 30 days)
    start_date = date.today() - timedelta(days=30)
    attendance_records = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        Attendance.date >= start_date
    ).all()
    
    total_days = 30
    present_days = sum(1 for a in attendance_records if a.status == 'Present')
    absent_days = sum(1 for a in attendance_records if a.status == 'Absent')
    late_days = sum(1 for a in attendance_records if a.status == 'Late')
    
    attendance_rate = (present_days / total_days) * 100 if total_days > 0 else 0
    
    # Calculate performance score (0-100)
    performance_score = attendance_rate * 0.7  # 70% weight on attendance
    if late_days == 0:
        performance_score += 20  # Bonus for no late days
    if absent_days == 0:
        performance_score += 10  # Bonus for perfect attendance
    
    performance_score = min(100, performance_score)
    
    # Generate recommendation
    if performance_score >= 90:
        recommendation = f"{employee.full_name} is performing excellently. Consider recognition or advancement opportunities."
    elif performance_score >= 75:
        recommendation = f"{employee.full_name} is performing well. Continue current practices."
    elif performance_score >= 60:
        recommendation = f"{employee.full_name} may benefit from additional support or training."
    else:
        recommendation = f"{employee.full_name} requires attention. Consider performance review and improvement plan."
    
    return {
        'success': True,
        'performance_score': round(performance_score, 1),
        'attendance_summary': {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'attendance_rate': round(attendance_rate, 1)
        },
        'recommendation': recommendation,
        'employee_name': employee.full_name,
        'employee_id': employee.id
    }


def _analyze_department(employees, label='Department'):
    """Analyze department or all staff performance."""
    total_employees = len(employees)
    if total_employees == 0:
        return {
            'success': False,
            'error': 'No employees to analyze',
            'performance_score': 0.0,
            'attendance_summary': {},
            'recommendation': ''
        }
    
    start_date = date.today() - timedelta(days=30)
    total_days = 30
    
    total_present = 0
    total_absent = 0
    total_late = 0
    individual_scores = []
    
    for employee in employees:
        attendance_records = Attendance.query.filter(
            Attendance.employee_id == employee.id,
            Attendance.date >= start_date
        ).all()
        
        present_days = sum(1 for a in attendance_records if a.status == 'Present')
        absent_days = sum(1 for a in attendance_records if a.status == 'Absent')
        late_days = sum(1 for a in attendance_records if a.status == 'Late')
        
        total_present += present_days
        total_absent += absent_days
        total_late += late_days
        
        attendance_rate = (present_days / total_days) * 100 if total_days > 0 else 0
        score = attendance_rate * 0.7
        if late_days == 0:
            score += 20
        if absent_days == 0:
            score += 10
        individual_scores.append(min(100, score))
    
    avg_performance_score = mean(individual_scores) if individual_scores else 0
    overall_attendance_rate = (total_present / (total_employees * total_days)) * 100 if total_employees > 0 else 0
    
    # Generate recommendation
    if avg_performance_score >= 85:
        recommendation = f"{label} performance is excellent. Maintain current standards."
    elif avg_performance_score >= 70:
        recommendation = f"{label} performance is good. Focus on continuous improvement."
    else:
        recommendation = f"{label} performance needs attention. Consider training and support initiatives."
    
    return {
        'success': True,
        'performance_score': round(avg_performance_score, 1),
        'attendance_summary': {
            'total_employees': total_employees,
            'total_days': total_days,
            'total_present': total_present,
            'total_absent': total_absent,
            'total_late': total_late,
            'overall_attendance_rate': round(overall_attendance_rate, 1)
        },
        'recommendation': recommendation,
        'label': label
    }

