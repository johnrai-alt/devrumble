"""
Django settings for the SadakSathi backend.

This mirrors src/config/env.js from the original Express project: required
env vars are validated at import time (fail fast on boot, same behaviour as
the JS `env.js`), and everything else reads from `.env` via python-decouple.
"""
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# --- required env vars (fail fast, same as env.js `required` list) ---
_REQUIRED = [
    "PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE",
    "JWT_ACCESS_SECRET", "JWT_REFRESH_SECRET",
]
_missing = [key for key in _REQUIRED if config(key, default=None) in (None, "")]
if _missing:
    raise RuntimeError(f"Missing required env vars: {', '.join(_missing)}")

SECRET_KEY = config("DJANGO_SECRET_KEY", default=config("JWT_ACCESS_SECRET"))
NODE_ENV = config("NODE_ENV", default="development")  # kept name for parity with env.js
DEBUG = NODE_ENV != "production"

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())

# Installed applications (Standard PostgreSQL setup)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'channels',
    'accounts',
    'incidents',
    'traffic',
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # i18n switcher for NP/Eng UI
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = "sadaksathi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    },
]

WSGI_APPLICATION = "sadaksathi.wsgi.application"
ASGI_APPLICATION = "sadaksathi.asgi.application"

# --- Database (Standard PostgreSQL) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # Standard PostgreSQL driver
        'NAME': config('PGDATABASE', default='sadaksathi'),
        'USER': config('PGUSER', default='postgres'),
        'PASSWORD': config('PGPASSWORD', default='changeme'),
        'HOST': config('PGHOST', default='localhost'),
        'PORT': config('PGPORT', default='5432'),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Internationalization & Timezones ---
USE_TZ = True
USE_I18N = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en"

LANGUAGES = (
    ('en', 'English'),
    ('ne', 'Nepali'),
)

# Fixed typo: changed LOCAL_PATHS to Django's required LOCALE_PATHS
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

STATIC_URL = "static/"

# Incident report photos, profile avatars, etc.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- Redis ---
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

# --- JWT ---
JWT_ACCESS_SECRET = config("JWT_ACCESS_SECRET")
JWT_REFRESH_SECRET = config("JWT_REFRESH_SECRET")
JWT_ACCESS_TTL = timedelta(minutes=15)
JWT_REFRESH_TTL_DAYS = 30
JWT_ALGORITHM = "HS256"

# --- OTP ---
OTP_TTL_MINUTES = 5
OTP_MAX_ATTEMPTS = 5

# --- SMS Provider ---
TWILIO_SID = config("TWILIO_SID", default="")
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN", default="")
TWILIO_FROM_NUMBER = config("TWILIO_FROM_NUMBER", default="")

# --- Third-Party Providers ---
GOOGLE_TRAFFIC_API_KEY = config("GOOGLE_TRAFFIC_API_KEY", default="")

BCRYPT_ROUNDS = 12

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "EXCEPTION_HANDLER": "accounts.exceptions.app_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "accounts.throttling.GlobalRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "global": "300/15m",
        "otp_request": "10/1h",
        "incident_create": "20/10m",
        "vote": "60/10m",
    },
}

# --- Celery ---
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}