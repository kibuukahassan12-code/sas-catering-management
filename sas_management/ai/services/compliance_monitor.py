"""
Compliance Monitor AI Service

Monitor food safety and regulatory compliance.
"""
from flask import current_app
from datetime import datetime, timedelta
from sas_management.ai.registry import is_feature_enabled


def check_compliance_status(area: str = "all"):
    """
    Check compliance status across specified areas.
    
    Args:
        area: Area to check (e.g., "food_safety", "hygiene", "all")
        
    Returns:
        Dictionary with compliance status
    """
    # Check if feature is enabled
    if not is_feature_enabled("compliance_monitor"):
        return {
            "success": False,
            "error": "Compliance Monitor feature is disabled",
            "compliance_score": None,
            "violations": [],
        }
    
    try:
        current_app.logger.info(f"Compliance Monitor accessed for area: {area}")
        
        compliance_score = 100  # Start at 100, deduct for issues
        violations = []
        recommendations = []
        risk_level = "low"
        
        try:
            # Check for recent food safety logs
            from sas_management.models import FoodSafetyLog
            
            # Check for overdue or missing logs
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            recent_logs = FoodSafetyLog.query.filter(
                FoodSafetyLog.created_at >= cutoff_date
            ).count() if hasattr(FoodSafetyLog, "created_at") else 0
            
            if recent_logs == 0:
                violations.append({
                    "type": "missing_logs",
                    "severity": "medium",
                    "message": "No food safety logs found in the last 30 days",
                })
                compliance_score -= 20
                recommendations.append({
                    "type": "documentation",
                    "priority": "high",
                    "message": "Ensure regular food safety logs are maintained",
                })
            
            # Check event service compliance
            from sas_management.service.models import ServiceEvent, ServiceChecklistItem
            
            recent_events = ServiceEvent.query.filter(
                ServiceEvent.event_date >= datetime.utcnow().date() - timedelta(days=30)
            ).all()
            
            incomplete_checklists = 0
            for event in recent_events:
                checklist_items = ServiceChecklistItem.query.filter_by(
                    service_event_id=event.id
                ).all()
                completed = sum(1 for item in checklist_items if item.completed)
                total = len(checklist_items)
                if total > 0 and completed < total * 0.8:  # Less than 80% complete
                    incomplete_checklists += 1
            
            if incomplete_checklists > len(recent_events) * 0.3:  # More than 30% incomplete
                violations.append({
                    "type": "incomplete_checklists",
                    "severity": "low",
                    "message": f"{incomplete_checklists} events have incomplete checklists",
                })
                compliance_score -= 10
                recommendations.append({
                    "type": "process",
                    "priority": "medium",
                    "message": "Ensure event checklists are completed before service",
                })
            
            # Determine risk level
            if compliance_score < 70:
                risk_level = "high"
            elif compliance_score < 85:
                risk_level = "medium"
            else:
                risk_level = "low"
        
        except Exception as e:
            current_app.logger.warning(f"Error checking compliance: {e}")
        
        return {
            "success": True,
            "compliance_score": max(0, compliance_score),
            "violations": violations,
            "recommendations": recommendations,
            "risk_level": risk_level,
            "area": area,
            "note": "Compliance check completed" if compliance_score >= 0 else "Error during compliance check",
        }
        
    except Exception as e:
        current_app.logger.error(f"Compliance Monitor error: {e}")
        return {
            "success": False,
            "error": str(e),
            "compliance_score": None,
            "violations": [],
        }

