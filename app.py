"""
Vercel-compatible Flask application entrypoint.
This file exposes the Flask app for Vercel serverless deployment.
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from sas_management
from sas_management.app import app

# Vercel requires the app instance to be named 'app'
# The app is already imported above

# Note: Do NOT call app.run() - Vercel handles serverless execution
