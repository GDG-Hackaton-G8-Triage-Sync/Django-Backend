import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_host(value: str) -> str:
    """Normalize host values for ALLOWED_HOSTS (strip scheme/path/port)."""
    value = value.strip()
    if not value:
        return ""
    if "://" in value:
        parsed = urlparse(value)
        return parsed.hostname or ""
    if "/" in value:
        parsed = urlparse(f"https://{value}")
        return parsed.hostname or ""
    return value.split(":")[0]

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
# Default to False in code; enable DEBUG explicitly via environment for development only.
DEBUG = env_bool("DJANGO_DEBUG", False)

raw_allowed_hosts = env_list("DJANGO_ALLOWED_HOSTS", ["127.0.0.1", "localhost"])
normalized_allowed_hosts = [normalize_host(host) for host in raw_allowed_hosts]

# Render sets this automatically for web services.
render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_hostname:
    normalized_allowed_hosts.append(render_hostname)

# Django's test client uses 'testserver' as the default HTTP_HOST for integration tests.
normalized_allowed_hosts.append('testserver')

# Keep order but remove duplicates/empties.
ALLOWED_HOSTS = list(dict.fromkeys([host for host in normalized_allowed_hosts if host]))

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    # Enable token blacklist support for rotating refresh tokens
    "rest_framework_simplejwt.token_blacklist",
    "triagesync_backend.apps.core",
    "triagesync_backend.apps.authentication",
    "triagesync_backend.apps.patients",
    "triagesync_backend.apps.triage",
    "triagesync_backend.apps.realtime",
    "triagesync_backend.apps.dashboard",
    "triagesync_backend.apps.api_admin",
    "triagesync_backend.apps.notifications",
    "drf_spectacular",
]

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "triagesync_backend.apps.core.middleware.payload_sanitizer.PayloadSanitizerMiddleware",
]

ROOT_URLCONF = "triagesync_backend.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "triagesync_backend.config.wsgi.application"
ASGI_APPLICATION = "triagesync_backend.config.asgi.application"


database_url = os.getenv("DATABASE_URL")

if database_url:
    tmpPostgres = urlparse(database_url)
    db_name = tmpPostgres.path.replace("/", "")
    
    # Always use PostgreSQL - no SQLite fallback
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": tmpPostgres.username,
            "PASSWORD": tmpPostgres.password,
            "HOST": tmpPostgres.hostname,
            "PORT": tmpPostgres.port or 5432,
            "OPTIONS": dict(parse_qsl(tmpPostgres.query)),
            # Keep DB connections open for a short time to improve performance
            # under ASGI/Daphne. Controlled via DB_CONN_MAX_AGE (seconds).
            "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        }
    }
else:
    # Enforce PostgreSQL - DATABASE_URL is required
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "PostgreSQL is the only supported database. "
        "Please set DATABASE_URL to your PostgreSQL connection string."
    )


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
# Directory where `collectstatic` will gather static files for production
# Use Path for BASE_DIR (pathlib.Path) so this works on all platforms.
STATIC_ROOT = BASE_DIR / "staticfiles"
# Optional: include a project-level `static/` folder during development
STATICFILES_DIRS = []
project_static_dir = BASE_DIR / "static"

if project_static_dir.exists():
    STATICFILES_DIRS.append(project_static_dir)
    
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "authentication.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "triagesync_backend.apps.core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "triagesync_backend.apps.core.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_DAYS", "1"))),
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Rotate refresh tokens and blacklist old ones to reduce token replay risk
    "ROTATE_REFRESH_TOKENS": env_bool("ROTATE_REFRESH_TOKENS", True),
    "BLACKLIST_AFTER_ROTATION": env_bool("BLACKLIST_AFTER_ROTATION", True),
}

REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    # Fallback for local dev without Redis - not suitable for multi-process deployments
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

# --- Celery Configuration ---
# Celery broker URL (uses Redis)
CELERY_BROKER_URL = REDIS_URL or 'redis://localhost:6379/0'
# Celery result backend (uses Redis)
CELERY_RESULT_BACKEND = REDIS_URL or 'redis://localhost:6379/0'
# Celery task serialization
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
# Celery timezone
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# -------------------- Production security defaults --------------------
# Only enable strict production settings when DEBUG is False. Environment
# variables can override individual behaviours if needed.
if not DEBUG:
    # Redirect HTTP → HTTPS. Default to enabled only when Render provides
    # a hostname (so local development without HTTPS isn't forced to redirect).
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", bool(render_hostname))

    # Set HSTS for browsers
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)

    # Cookies
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)
    SESSION_COOKIE_HTTPONLY = env_bool("SESSION_COOKIE_HTTPONLY", True)

    # X-Frame-Options and related headers
    X_FRAME_OPTIONS = os.getenv("X_FRAME_OPTIONS", "DENY")
    SECURE_CONTENT_TYPE_NOSNIFF = env_bool("SECURE_CONTENT_TYPE_NOSNIFF", True)
    SECURE_BROWSER_XSS_FILTER = env_bool("SECURE_BROWSER_XSS_FILTER", True)

    # If deployment sits behind a proxy (Render), honor X-Forwarded-Proto
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

else:
    # Development-friendly defaults
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", False)
    SESSION_COOKIE_HTTPONLY = env_bool("SESSION_COOKIE_HTTPONLY", True)


# --- Gemini / AI service tuning -------------------------------------------
# Total attempts per model (not retries-after-initial). Value N means N calls.
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
# Per-call wall-clock budget before we abandon this model and move on.
# Default of 30 seconds accommodates typical Gemini API response times.
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "30"))
# Explicit allow-list; replaces the old 'flash in name' heuristic.
# Each model has an independent free-tier quota, so the more we list, the more
# resilient the pipeline is when one model's daily limit is exhausted. Order is
# tried left-to-right; models not enabled for the current API key are filtered
# out at runtime by _resolve_model_priority().
GEMINI_MODEL_PRIORITY = env_list("GEMINI_MODEL_PRIORITY") or [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]
# TTL for cached list_models() output (seconds).
GEMINI_MODEL_LIST_TTL_SECONDS = int(os.getenv("GEMINI_MODEL_LIST_TTL_SECONDS", "600"))
# Circuit breaker: after N consecutive full-call failures, open the circuit
# and short-circuit to the rule-based fallback for COOLDOWN_SECONDS.
GEMINI_CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("GEMINI_CIRCUIT_BREAKER_THRESHOLD", "5"))
GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS = int(os.getenv("GEMINI_CIRCUIT_BREAKER_COOLDOWN_SECONDS", "30"))

# --- Logging Configuration ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
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
        'triagesync_backend.apps.realtime.middleware': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'triagesync_backend.apps.realtime.consumers': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# --- Swagger / OpenAPI Configuration ---
SPECTACULAR_SETTINGS = {
    "TITLE": "TriageSync API",
    "DESCRIPTION": "API documentation for TriageSync backend",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_PATCH": True,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
}




