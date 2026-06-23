"""
ASGI config for crm1 project.
<<<<<<< HEAD
Defaults to dev settings; set DJANGO_SETTINGS_MODULE env var for production.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm1.settings.dev')
=======

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm1.settings")

>>>>>>> bda2651b2d659a1fa8eddca086b4a11b677495ca
application = get_asgi_application()
