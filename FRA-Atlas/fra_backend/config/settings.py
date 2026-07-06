"""Django settings for the FRA Atlas backend.

Twelve-factor: every environment-specific value comes from the environment, so
the same container image runs in dev (SQLite/SpatiaLite, locmem cache) and in
production (PostgreSQL/PostGIS + Redis + S3) with no code changes.
"""
import os
from datetime import timedelta
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    return os.environ.get(key, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(key, default=""):
    raw = os.environ.get(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-key-change-in-production")
if not DEBUG and SECRET_KEY == "dev-insecure-key-change-in-production":
    raise RuntimeError("DJANGO_SECRET_KEY must be set when DEBUG is off.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "*" if DEBUG else "")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ALLOW_CREDENTIALS = True
AUDIT_LOG_SECRET = env("AUDIT_LOG_SECRET", "dev-audit-secret-rotate-me")
USE_GIS = env_bool("USE_GIS", True)
SPATIALITE_LIBRARY_PATH = env("SPATIALITE_LIBRARY_PATH", "mod_spatialite")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "apps.common",
    "apps.accounts",
    "apps.geo",
    "apps.claims",
    "apps.audit",
    "apps.analytics",
    "apps.documents",
    "apps.reports",
    "apps.ops",
    "apps.sync",
    "apps.privacy",
    "django_prometheus",
    "drf_spectacular",
    "corsheaders",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.RequestContextMiddleware",
    "apps.common.api_hardening.RequestLoggingMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    },
]

if env("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.config(
        conn_max_age=int(env("DB_CONN_MAX_AGE", "600")), conn_health_checks=True)}
    if "postgis" in env("DATABASE_URL") or USE_GIS:
        DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"
elif USE_GIS:
    DATABASES = {"default": {"ENGINE": "django.contrib.gis.db.backends.spatialite",
                             "NAME": BASE_DIR / "db.sqlite3"}}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3",
                             "NAME": BASE_DIR / "db.sqlite3"}}

REDIS_URL = env("REDIS_URL")
if REDIS_URL:
    CACHES = {"default": {"BACKEND": "django_redis.cache.RedisCache",
                          "LOCATION": REDIS_URL,
                          "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"}}}
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

AUTH_USER_MODEL = "accounts.User"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.TimestampCursorPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": ["apps.common.api_hardening.RoleRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"user": "1000/min", "anon": "60/min"},
    "EXCEPTION_HANDLER": "apps.common.errors.standardized_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "sub",
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FRA Atlas Decision Support API",
    "DESCRIPTION": "Forest Rights Act Atlas backend - claims, geospatial, risk analytics.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MEDIA_ROOT = env("MEDIA_ROOT", str(BASE_DIR / "media"))

STORAGE_BACKEND = env("STORAGE_BACKEND", "local")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", "")
AV_SCANNER = env("AV_SCANNER", "noop")
CLAMAV_HOST = env("CLAMAV_HOST", "clamav")
CLAMAV_PORT = int(env("CLAMAV_PORT", "3310"))
OCR_ENGINE = env("OCR_ENGINE", "noop")

RETENTION_YEARS = int(env("RETENTION_YEARS", "7"))
ENCRYPTION_ACTIVE_VERSION = int(env("ENCRYPTION_ACTIVE_VERSION", "1"))
ENCRYPTION_KEYS = {1: env("ENCRYPTION_KEY_V1", "2b80PNHyJROYAZhUjOkGXyOKftzi7IRbMY0qg3XwqAU=")}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", REDIS_URL or "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", REDIS_URL or "cache+memory://")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_DEFAULT_RETRY_DELAY = 5
CELERY_TASK_MAX_RETRIES = 5
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
    "loggers": {"fra.requests": {"handlers": ["console"], "level": "INFO", "propagate": False}},
}
