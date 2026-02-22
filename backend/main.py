"""
Backend entrypoint for Vercel deployment.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app from sas_management
from sas_management.app import app
