import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "GS_SECRET_KEY",
    "django-insecure-o1tk09gr_g=c06o9t6%jb5dy2!-(zz7rpan4x!-1@^say@k)(h",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = "GS_DEBUG" in os.environ

ALLOWED_HOSTS = ["*"] if DEBUG else [os.environ.get("GS_ALLOWED_HOST", "")]

if not DEBUG:
    # We only support HTTPS deployments
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

INSTALLED_APPS = [
    "splitzie.apps.SplitzieConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "splitzie.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "splitzie.wsgi.application"

# SQLite is not supported because it does not have a decimal type
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("GS_DB_NAME", ""),
        "USER": os.environ.get("GS_DB_USER", ""),
        "PASSWORD": os.environ.get("GS_DB_PASSWORD", ""),
        "HOST": os.environ.get("GS_DB_HOST", ""),
        "PORT": os.environ.get("GS_DB_PORT", ""),
        "CONN_MAX_AGE": 3600,
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "nl"
# LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en", _("English")),
    ("nl", _("Dutch")),
]

TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True
FORMAT_MODULE_PATH = "splitzie.formats"

STATIC_ROOT = os.environ.get("GS_STATIC_ROOT")
STATIC_URL = os.environ.get("GS_STATIC_URL", "static/")

MEDIA_ROOT = os.environ.get("GS_MEDIA_ROOT", "media/")
MEDIA_URL = os.environ.get("GS_MEDIA_URL", "media/")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEFAULT_FROM_EMAIL = os.environ.get("GS_EMAIL_FROM", "webmaster@localhost")
SERVER_EMAIL = os.environ.get("GS_EMAIL_FROM", "root@localhost")
if "GS_EMAIL_HOST" in os.environ:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get("GS_EMAIL_HOST", "localhost")
    EMAIL_PORT = int(os.environ.get("GS_EMAIL_PORT")) or 25
    EMAIL_HOST_USER = os.environ.get("GS_EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("GS_EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = "GS_EMAIL_USE_TLS" in os.environ
    EMAIL_USE_SSL = "GS_EMAIL_USE_SSL" in os.environ
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# The base URL of this deployment, without trailing /.
BASE_URL = os.environ.get("GS_BASE_URL", "http://localhost:8000")

# If (and only if!) we're behind a proxy that sets X-Forwarded-Proto correctly,
# enable this setting to make use of the header.
if "GS_PROXY_SSL" in os.environ:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
