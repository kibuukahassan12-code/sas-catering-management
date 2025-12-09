"""
Password generation utilities for SAS Management System.
"""
import secrets
import string


def generate_secure_password(length=12):
    """
    Generate a secure random password.
    
    Args:
        length: Length of the password (default: 12)
    
    Returns:
        A secure random password string
    """
    # Use letters (uppercase and lowercase), digits, and safe special characters
    chars = string.ascii_letters + string.digits + "!@#$%&*?"
    return ''.join(secrets.choice(chars) for _ in range(length))

