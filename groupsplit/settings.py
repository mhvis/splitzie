import os

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "GS_SECRET_KEY", "django-insecure-o1tk09gr_g=c06o9t6%jb5dy2!-(zz7rpan4x!-1@^say@k)(h"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = "GS_DEBUG" in os.environ

ALLOWED_HOSTS = ["*"] if DEBUG else [os.environ["GS_ALLOWED_HOST"]]

if not DEBUG:
    # We only support HTTPS deployments
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True


INSTALLED_APPS = [
    "groupsplit.apps.GroupSplitConfig",
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
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "groupsplit.urls"

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

WSGI_APPLICATION = "groupsplit.wsgi.application"


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

# LANGUAGE_CODE = 'nl-nl'
LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Amsterdam"

USE_I18N = True

USE_TZ = True


STATIC_ROOT = os.environ.get("GS_STATIC_ROOT")
STATIC_URL = os.environ.get("GS_STATIC_URL", "static/")

MEDIA_ROOT = os.environ.get("GS_MEDIA_ROOT", "media/")
MEDIA_URL = os.environ.get("GS_MEDIA_URL", "media/")


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
