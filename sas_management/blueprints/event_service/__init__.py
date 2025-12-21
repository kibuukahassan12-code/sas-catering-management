"""
Event Service Blueprint Module

This module exports the event_service blueprint for registration in app.py.
"""
from sas_management.blueprints.event_service.routes import event_service_bp

__all__ = ['event_service_bp']

