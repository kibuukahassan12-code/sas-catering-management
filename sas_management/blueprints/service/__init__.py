"""
Service Blueprint Module

This module re-exports the service blueprint from routes.py to ensure
a single source of truth and prevent duplicate blueprint definitions.
"""

# Import the blueprint from routes.py - this is the canonical definition
from sas_management.blueprints.service.routes import service_bp

# Re-export for convenience
__all__ = ['service_bp']
