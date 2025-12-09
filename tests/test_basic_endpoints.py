"""Basic endpoint tests for SAS Management System."""
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_home(client):
    """Test home/root endpoint."""
    rv = client.get('/')
    assert rv.status_code in (200, 302), f"Expected 200 or 302, got {rv.status_code}"

def test_floorplanner_dashboard(client):
    """Test floorplanner dashboard endpoint."""
    rv = client.get('/floorplanner/dashboard')
    assert rv.status_code in (200, 302, 401), f"Expected 200, 302, or 401, got {rv.status_code}"

def test_analytics_dashboard(client):
    """Test analytics dashboard endpoint."""
    rv = client.get('/analytics/dashboard')
    assert rv.status_code in (200, 302, 401), f"Expected 200, 302, or 401, got {rv.status_code}"

def test_search_endpoint(client):
    """Test search endpoint."""
    rv = client.get('/search')
    assert rv.status_code in (200, 302, 401), f"Expected 200, 302, or 401, got {rv.status_code}"

def test_pwa_test_endpoint(client):
    """Test PWA test endpoint."""
    rv = client.get('/pwa-test')
    assert rv.status_code in (200, 302, 401), f"Expected 200, 302, or 401, got {rv.status_code}"

