import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

print("CWD:", os.getcwd())
print("BASE_DIR:", BASE_DIR)
print("ENV FILE EXISTS:", os.path.exists(BASE_DIR / ".env"))
print("DATABASE_URL:", os.environ.get("DATABASE_URL"))

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

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["127.0.0.1", "localhost"])

INSTALLED_APPS = [
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
    "triagesync_backend.apps.authentication",
    "triagesync_backend.apps.patients",
    "triagesync_backend.apps.triage",
    "triagesync_backend.apps.realtime",
    "triagesync_backend.apps.dashboard",
    "triagesync_backend.apps.core",
]

MIDDLEWARE = [
    "triagesync_backend.apps.triage.middleware.PayloadSanitizerMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "triagesync_backend.apps.core.middleware.RequestIDMiddleware",
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
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": tmpPostgres.path.replace("/", ""),
            "USER": tmpPostgres.username,
            "PASSWORD": tmpPostgres.password,
            "HOST": tmpPostgres.hostname,
            "PORT": tmpPostgres.port or 5432,
            "OPTIONS": dict(parse_qsl(tmpPostgres.query)),
        }
    }
else:
    # Local fallback for development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


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

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "authentication.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        }
    }
else:
    # Fallback for local dev without Redis — not suitable for multi-process deployments
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Gemini / AI service tuning -------------------------------------------
# Total attempts per model (not retries-after-initial). Value N means N calls.
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
# Per-call wall-clock budget before we abandon this model and move on.
GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "8"))
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
