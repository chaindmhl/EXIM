import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY environment variable is not set!")

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "exim-142442460469.asia-southeast1.run.app,.run.app").split(",")


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

AUTH_USER_MODEL = 'board_exam.CustomUser'


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

# --------------------------
# DATABASE
# --------------------------
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get("POSTGRES_DB"),
#         'USER': os.environ.get("POSTGRES_USER"),
#         'PASSWORD': os.environ.get("POSTGRES_PASSWORD"),
#         'HOST': os.environ.get("POSTGRES_HOST"),
#         'PORT': os.environ.get("POSTGRES_PORT", "5432"),
#     }
# }


DB_HOST = os.environ.get("DB_HOST")
if not DB_HOST:
    raise RuntimeError("DB_HOST environment variable is not set")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'electronic_board'),
        'USER': os.environ.get('DB_USER', 'admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'admin@03'),
        'HOST': f"/cloudsql/{DB_HOST}",
        'PORT': '5432',
    }
}



# --------------------------
# PASSWORD VALIDATION
# --------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------
# INTERNATIONALIZATION
# --------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# --------------------------
# STATIC FILES
# --------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --------------------------
# MEDIA FILES
# --------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --------------------------
# CSRF & SESSION SECURITY
# --------------------------
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG


