"""
Production settings — used on Render Free plan (and any similar platform).

Set this env var on Render:
    DJANGO_SETTINGS_MODULE=crm1.settings.prod

Required environment variables on Render:
    SECRET_KEY       — long random string
    DATABASE_URL     — auto-set by Render Postgres add-on
    ALLOWED_HOSTS    — your-app.onrender.com
    COMPANY_NAME, COMPANY_SHORT_NAME, COMPANY_TAGLINE — branding
    EMAIL_*          — SMTP credentials

Media files note (Render Free plan):
    Persistent Disk is a PAID feature. On the free plan, MEDIA_ROOT points
    to a directory inside the container — uploads work while the container
    is running but are wiped on every redeploy or restart.
    This is acceptable for a demo/pilot deployment.
    When you're ready for persistence, upgrade to a paid Render instance
    and add a Persistent Disk mounted at /opt/render/media, then set:
        MEDIA_ROOT=/opt/render/media  (env var on Render dashboard)

Never set DEBUG=True here.
"""
import os
from pathlib import Path
import dj_database_url
from .base import *  # noqa: F401, F403
from decouple import config, Csv

DEBUG = False

# ---------------------------------------------------------------------------
# Allowed hosts
# ---------------------------------------------------------------------------
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='.onrender.com',
    cast=Csv(),
)

# ---------------------------------------------------------------------------
# Database — Render injects DATABASE_URL automatically
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
    # Fallback for local prod testing without DATABASE_URL
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
# Media files — served via WhiteNoise on Render Free plan
# ---------------------------------------------------------------------------
# Product images are committed to git under static/images/.
# collectstatic copies them to staticfiles/images/.
# WhiteNoise serves staticfiles/ at /static/, so images are available at
# /static/images/menu/x.png.
#
# base.py sets MEDIA_URL='/images/' which works in dev (Django's static()
# helper maps /images/ → static/images/ when DEBUG=True).
# In production DEBUG=False so that helper is inactive — we override
# MEDIA_URL to '/static/images/' so product.image.url renders the correct
# path that WhiteNoise actually serves.
# ---------------------------------------------------------------------------
_media_env = os.environ.get('MEDIA_ROOT', '')
MEDIA_ROOT = Path(_media_env) if _media_env else BASE_DIR / 'static' / 'images'
try:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
except OSError:
    pass

MEDIA_URL = '/static/images/'

# ---------------------------------------------------------------------------
# Static files — Django 5.x STORAGES dict with WhiteNoise
# Using CompressedStaticFilesStorage (NOT Manifest) because the legacy
# assets/css/app.css references files (e.g. sprite-skin-flat.png) that
# don't exist in the static tree. The Manifest variant validates every
# CSS url() reference and hard-fails on missing files during collectstatic.
# CompressedStaticFilesStorage still gzips and brotli-compresses everything
# but skips the strict reference validation.
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
# ---------------------------------------------------------------------------
SESSION_COOKIE_AGE = 60 * 60 * 8
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

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
