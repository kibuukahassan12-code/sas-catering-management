"""Integrations blueprint for admin UI and webhooks."""
from flask import Blueprint
from .routes import integrations_bp

__all__ = ['integrations_bp']

