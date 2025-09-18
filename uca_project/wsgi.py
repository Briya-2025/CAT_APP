"""
WSGI config for uca_project project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uca_project.settings_production')

application = get_wsgi_application()
