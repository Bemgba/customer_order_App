"""
Development settings.
Uses PostgreSQL (same as prod — avoids "works on my machine" surprises).
Shows full Django error pages. No HTTPS enforcement.
Run with: DJANGO_SETTINGS_MODULE=crm1.settings.dev  (the default in manage.py)
"""
from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = True

# ---------------------------------------------------------------------------
# Static files — no manifest/hashing in dev (avoids collectstatic errors
# from broken references). Uses the new Django 5.x STORAGES dict.
# ---------------------------------------------------------------------------
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# ---------------------------------------------------------------------------
# Session security
# Sessions expire when the browser closes, and are limited to 8 hours max.
# Changing SECRET_KEY in .env will also invalidate all existing sessions,
# which is the correct behaviour after a redeployment.
# ---------------------------------------------------------------------------
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60 * 60 * 8   # 8 hours hard cap

# ---------------------------------------------------------------------------
# Database — PostgreSQL, credentials from .env
# Using the same engine as production ensures migrations behave identically.
# For a completely offline environment you can swap this back to SQLite.
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='foodvendordb'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# ---------------------------------------------------------------------------
# Email — real SMTP in dev so you can test password-reset flows immediately.
# All credentials come from .env (already set in base.py).
# To silence emails entirely during testing, uncomment the line below:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Logging — console output for development
# ---------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        # Uncomment to print every SQL query Django runs:
        # 'django.db.backends': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        #     'propagate': False,
        # },
        'accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
