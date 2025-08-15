from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# -------- Environment --------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-override")
DEBUG = os.environ.get("DEBUG", "False") == "True"

# Allow your Vercel domains (add your custom domain if any)
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "*,.vercel.app").split(",")]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "https://*.vercel.app").split(",")]

# -------- Apps / Middleware --------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "main",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve /static on Vercel
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "Full_web.urls"
WSGI_APPLICATION = "Full_web.wsgi.application"
ASGI_APPLICATION = "Full_web.asgi.application"

# -------- Sessions & Database (no persistent DB on Vercel) --------
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"  # avoid DB writes
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/tmp/app.sqlite3",  # ephemeral, OK for non-DB pages / health checks
    }
}

# -------- Templates --------
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# -------- Static files --------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -------- Email (env-driven; console in DEBUG) --------
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
    EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False") == "True"
    if EMAIL_USE_TLS and EMAIL_USE_SSL:
        raise ValueError("Configure either TLS(587) or SSL(465), not both")
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587" if EMAIL_USE_TLS else "465"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
    SERVER_EMAIL = os.environ.get("SERVER_EMAIL", EMAIL_HOST_USER)
    EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "30"))

# -------- Logging (shows in Vercel Function logs) --------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
