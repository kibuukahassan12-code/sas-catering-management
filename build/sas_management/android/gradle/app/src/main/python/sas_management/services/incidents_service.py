"""Incidents service."""
from flask import current_app

def escalate_incident(incident_id, action):
    """Escalate or resolve incident."""
    try:
        from models import Incident, db
        incident = Incident.query.get(incident_id)
        if not incident:
            return {'success': False, 'error': 'Incident not found'}
        
        if action == 'resolve':
            incident.status = 'resolved'
            incident.resolved_at = datetime.utcnow()
        elif action == 'escalate':
            if incident.severity == 'low':
                incident.severity = 'medium'
            elif incident.severity == 'medium':
                incident.severity = 'high'
            elif incident.severity == 'high':
                incident.severity = 'critical'
        
        db.session.commit()
        return {'success': True}
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error escalating incident: {e}")
        return {'success': False, 'error': str(e)}

