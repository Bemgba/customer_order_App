"""
Production settings — used on Render (and any similar platform).

Set this env var on Render:
    DJANGO_SETTINGS_MODULE=crm1.settings.prod

Required environment variables on Render:
    SECRET_KEY       — long random string
    DATABASE_URL     — auto-set by Render Postgres add-on
    ALLOWED_HOSTS    — your-app.onrender.com  (or leave blank to use the default below)
    MEDIA_ROOT       — mount path of the Render Persistent Disk, e.g. /opt/render/media
    COMPANY_NAME, COMPANY_SHORT_NAME, COMPANY_TAGLINE — branding
    EMAIL_*          — SMTP credentials

Never set DEBUG=True here.
"""
import os
from pathlib import Path
import dj_database_url
from .base import *  # noqa: F401, F403
from decouple import config, Csv

DEBUG = False

# ---------------------------------------------------------------------------
# Allowed hosts — always include Render's wildcard + your custom domain
# Reads ALLOWED_HOSTS from env (comma-separated), falls back to onrender.com
# ---------------------------------------------------------------------------
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='.onrender.com',
    cast=Csv(),
)

# ---------------------------------------------------------------------------
# Database — Render injects DATABASE_URL automatically when you attach a
# Postgres instance.  dj-database-url parses it into Django's DATABASES dict.
# CONN_MAX_AGE=60 keeps connections alive across requests (better throughput).
# ---------------------------------------------------------------------------
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
        )
    }
else:
    # Fallback: individual vars (local prod testing without DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 60,
            'OPTIONS': {'connect_timeout': 10},
        }
    }

# ---------------------------------------------------------------------------
# Session security
# ---------------------------------------------------------------------------
SESSION_COOKIE_AGE = 60 * 60 * 8   # 8 hours hard cap
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # required behind Render's proxy
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ---------------------------------------------------------------------------
# Media files — Render Persistent Disk
# ---------------------------------------------------------------------------
# On Render: attach a Persistent Disk and set its mount path, e.g. /opt/render/media
# Then add MEDIA_ROOT=/opt/render/media as an environment variable.
# MEDIA_URL stays '/images/' so existing template URLs keep working.
#
# If MEDIA_ROOT env var is not set (first deploy before disk is attached),
# falls back safely to BASE_DIR/media — change to disk path before going live.
# ---------------------------------------------------------------------------
_media_root_env = os.environ.get('MEDIA_ROOT', '')
if _media_root_env:
    MEDIA_ROOT = Path(_media_root_env)
else:
    MEDIA_ROOT = BASE_DIR / 'media'   # safe fallback, not persistent

# Ensure the media directory exists. Wrapped in try/except so collectstatic
# and migrate (which run before the disk is fully ready) don't fail.
try:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

# ---------------------------------------------------------------------------
# Logging — console only (Render captures stdout/stderr in the log viewer)
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
            'level': 'WARNING',
            'propagate': True,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
