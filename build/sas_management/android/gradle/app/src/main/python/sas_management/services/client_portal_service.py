"""Client Portal service."""
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

def generate_access_token():
    """Generate secure access token for client links."""
    return secrets.token_urlsafe(32)

def create_client_portal_user(client_id, email, password):
    """Create client portal user account."""
    try:
        from models import ClientPortalUser, db
        
        existing = ClientPortalUser.query.filter_by(email=email).first()
        if existing:
            return {'success': False, 'error': 'Email already registered'}
        
        user = ClientPortalUser(
            client_id=client_id,
            email=email,
            password_hash=generate_password_hash(password),
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        
        return {'success': True, 'user_id': user.id}
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error creating client portal user: {e}")
        return {'success': False, 'error': str(e)}

def authenticate_client(email, password):
    """Authenticate client portal user."""
    try:
        from models import ClientPortalUser
        
        user = ClientPortalUser.query.filter_by(email=email, is_active=True).first()
        if user and check_password_hash(user.password_hash, password):
            return {'success': True, 'user': user}
        return {'success': False, 'error': 'Invalid credentials'}
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error authenticating client: {e}")
        return {'success': False, 'error': str(e)}

def create_shareable_link(client_id, event_id):
    """Create shareable link for client to view event/quotes."""
    try:
        from models import ClientEventLink, db
        
        token = generate_access_token()
        link = ClientEventLink(
            client_id=client_id,
            event_id=event_id,
            access_token=token,
            status='pending'
        )
        db.session.add(link)
        db.session.commit()
        
        return {'success': True, 'token': token, 'link_id': link.id}
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error creating shareable link: {e}")
        return {'success': False, 'error': str(e)}

