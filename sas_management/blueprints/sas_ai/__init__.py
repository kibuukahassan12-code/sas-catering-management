"""
SAS AI Blueprint

Central hub for all AI features in the SAS Management System.
"""
from flask import Blueprint
from .routes import sas_ai_bp

__all__ = ['sas_ai_bp']

