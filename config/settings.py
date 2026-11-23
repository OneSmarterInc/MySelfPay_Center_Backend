import os
from pathlib import Path
import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
DEBUG = os.getenv('DJANGO_DEBUG', 'false').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY is required outside local development.')
    SECRET_KEY = 'center-pro-local-development-only'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
ENABLE_DEV_LOGIN = DEBUG and os.getenv('ENABLE_DEV_LOGIN', 'false').lower() == 'true'
database_url = os.getenv('DATABASE_URL', '')
if not database_url and not DEBUG:
    raise ImproperlyConfigured('Production requires a PostgreSQL DATABASE_URL.')
if database_url:
    DATABASES = {'default': dj_database_url.parse(database_url, conn_max_age=60)}
    if DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
        raise ImproperlyConfigured('DATABASE_URL must use PostgreSQL.')
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'development.sqlite3'}}
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'rest_framework', 'center_pro']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
TIME_ZONE = 'UTC'
APPEND_SLASH = False
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'], 'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'], 'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'], 'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser']}
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:5173,http://localhost:5173').split(',')
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://127.0.0.1:5173').rstrip('/')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@example.invalid')
EMAIL_TIMEOUT = 10
SECURE_REFERRER_POLICY = 'no-referrer'

DATA_UPLOAD_MAX_MEMORY_SIZE = 100000
if not DEBUG:
    from urllib.parse import urlparse
    origin = urlparse(FRONTEND_ORIGIN)
    if origin.scheme != 'https' or not origin.netloc or origin.path:
        raise ImproperlyConfigured('Production FRONTEND_ORIGIN must be an HTTPS origin without a path.')
    DATABASES['default'].setdefault('OPTIONS', {}).setdefault('sslmode', 'require')
