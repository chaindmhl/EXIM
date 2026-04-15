import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------
# SECRET KEY
# -------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-t&ri-woq=wx@da@jwe%#soj(9ri9un%b@yzx3aq!m@g#q-*@n1"
)

if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY environment variable is not set!")

# -------------------------
# DEBUG / HOSTS
# -------------------------
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "exim-app-142442460469.asia-southeast1.run.app,.run.app"
).split(",")

# -------------------------
# API KEYS
# -------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# -------------------------
# AUTH
# -------------------------
AUTH_USER_MODEL = 'board_exam.CustomUser'
LOGIN_URL = '/login/'

# --------------------------
# APPLICATION DEFINITION
# --------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'board_exam',

    "whitenoise.runserver_nostatic",
]

# -------------------------
# REST FRAMEWORK
# -------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# -------------------------
# MIDDLEWARE
# -------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Electronic_exam.urls'

# -------------------------
# TEMPLATES
# -------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Electronic_exam.wsgi.application'

# -------------------------
# DATABASE (SQLite for Cloud Run)
# -------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',
    }
}

# -------------------------
# PASSWORD VALIDATION
# -------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------
# INTERNATIONALIZATION
# -------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

# -------------------------
# STATIC FILES
# -------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -------------------------
# MEDIA FILES (REMOVED FOR FIREBASE STORAGE)
# -------------------------
# ❌ DO NOT USE LOCAL MEDIA OR GCS MEDIA SETTINGS ANYMORE
# Firebase Storage handles this externally

# -------------------------
# SECURITY
# -------------------------
CSRF_COOKIE_HTTPONLY = True
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG