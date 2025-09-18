"""
ASGI config for uca_project project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uca_project.settings_production')

application = get_asgi_application()
