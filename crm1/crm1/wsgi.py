"""
WSGI config for crm1 project.
Defaults to dev settings; set DJANGO_SETTINGS_MODULE=crm1.settings.prod
in the hosting environment for production.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm1.settings.dev')

application = get_wsgi_application()
