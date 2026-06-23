#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Default to dev settings; override with DJANGO_SETTINGS_MODULE env var
    # e.g. for production: set DJANGO_SETTINGS_MODULE=crm1.settings.prod
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm1.settings.dev')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


<<<<<<< HEAD
if __name__ == '__main__':
=======
if __name__ == "__main__":
>>>>>>> bda2651b2d659a1fa8eddca086b4a11b677495ca
    main()
