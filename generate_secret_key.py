#!/usr/bin/env python3
"""
Generate a secure Django SECRET_KEY for production use.
"""

import secrets
import string

def generate_secret_key():
    """Generate a secure Django SECRET_KEY."""
    # Use Django's default character set for SECRET_KEY
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))

if __name__ == '__main__':
    secret_key = generate_secret_key()
    print(f"Generated SECRET_KEY: {secret_key}")
    print(f"\nAdd this to your environment variables:")
    print(f"export SECRET_KEY='{secret_key}'")
