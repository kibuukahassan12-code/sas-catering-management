"""
Staff Performance Coach AI Service

AI-powered staff performance analysis and coaching.
"""
from flask import current_app
from sas_management.ai.registry import is_feature_enabled


def get_staff_coaching_recommendations(staff_id: int = None):
    """
    Get personalized coaching recommendations for staff.
    
    Args:
        staff_id: Staff member ID
        
    Returns:
        Dictionary with coaching recommendations
    """
    # Check if feature is enabled
    if not is_feature_enabled("staff_coach"):
        return {
            "success": False,
            "error": "Staff Coach feature is disabled",
            "performance_summary": {},
            "coaching_recommendations": [],
        }
    
    try:
        current_app.logger.info(f"Staff Coach accessed for staff: {staff_id}")
        
        performance_summary = {}
        coaching_recommendations = []
        strengths = []
        improvement_areas = []
        
        try:
            from sas_management.models import User, ServiceStaffAssignment
            
            if staff_id:
                staff = User.query.get(staff_id)
                if staff:
                    # Analyze staff assignments
                    assignments = ServiceStaffAssignment.query.filter_by(
                        staff_id=staff_id
                    ).all()
                    
                    if assignments:
                        # Basic performance metrics
                        total_assignments = len(assignments)
                        roles = {}
                        for assignment in assignments:
                            role = assignment.role or "General"
                            roles[role] = roles.get(role, 0) + 1
                        
                        performance_summary = {
                            "total_assignments": total_assignments,
                            "primary_roles": dict(sorted(roles.items(), key=lambda x: x[1], reverse=True)[:3]),
                        }
                        
                        # Generate recommendations
                        if total_assignments < 5:
                            coaching_recommendations.append({
                                "type": "experience",
                                "priority": "medium",
                                "message": "Consider assigning more events to build experience",
                            })
                        
                        most_common_role = max(roles.items(), key=lambda x: x[1])[0] if roles else None
                        if most_common_role:
                            strengths.append(f"Experienced in {most_common_role} role")
        
        except Exception as e:
            current_app.logger.warning(f"Error analyzing staff: {e}")
        
        return {
            "success": True,
            "performance_summary": performance_summary,
            "coaching_recommendations": coaching_recommendations,
            "strengths": strengths,
            "improvement_areas": improvement_areas,
            "note": "Analysis based on assignment history" if performance_summary else "Insufficient data for analysis",
        }
        
    except Exception as e:
        current_app.logger.error(f"Staff Coach error: {e}")
        return {
            "success": False,
            "error": str(e),
            "performance_summary": {},
            "coaching_recommendations": [],
        }

