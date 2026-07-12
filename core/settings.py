from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# GDAL/GEOS (required for django.contrib.gis on Ubuntu)
GDAL_LIBRARY_PATH = os.environ.get(
    'GDAL_LIBRARY_PATH', '/usr/lib/x86_64-linux-gnu/libgdal.so'
)
GEOS_LIBRARY_PATH = os.environ.get(
    'GEOS_LIBRARY_PATH', '/usr/lib/x86_64-linux-gnu/libgeos_c.so'
)

SECRET_KEY = 'django-insecure-=9xl#&msc(zpz=i91=&@(oy6)0cwntgict4@e3jzts#drdghbt'
DEBUG = True
# Accept any Host header (typical behind a reverse proxy or for EC2 public IP).
# For stricter production, set DJANGO_ALLOWED_HOSTS to a comma-separated list instead.
ALLOWED_HOSTS = ['*']

# Base URL of this API for clients and helper scripts (no trailing slash).
# Example production: http://16.16.160.64:8000
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'rest_framework_simplejwt.token_blacklist',
    # channels removed
    # Project apps
    'users',
    'billboards',
    'notifications',
    'admin_panel',
    'locations',
    'chat',
    'bookings',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # Enable response compression for better performance
    'core.middleware.CloseOldConnectionsMiddleware',  # Close old DB connections to prevent pool exhaustion
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'postgres',
        'USER': 'postgres.tdfqrvzhfrkriuhbwnkf',
        'PASSWORD': 'zeshanopn1613m',
        'HOST': 'aws-1-ap-southeast-1.pooler.supabase.com',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 5,  # Reduced timeout to fail fast
            'options': '-c statement_timeout=30000',  # Reduced statement timeout
        },
        # Session pooler (port 5432) allows ~15 clients — keep 0 unless using transaction pooler (6543).
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '0')),
        'CONN_HEALTH_CHECKS': True,
        'ATOMIC_REQUESTS': False,  # Don't wrap each request in a transaction
    }
}

# Local/offline: set DJANGO_USE_SQLITE=1 to use SQLite (migrate + smoke tests without Postgres).
if os.environ.get('DJANGO_USE_SQLITE') == '1':
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
os.makedirs(MEDIA_ROOT / 'billboards', exist_ok=True)


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Firebase Cloud Messaging Configuration
# Prefer firebase-service-account.json; also accept the Console download name.
_firebase_default = BASE_DIR / 'firebase-service-account.json'
_firebase_adminsdk = next(BASE_DIR.glob('*firebase-adminsdk*.json'), None)
FIREBASE_CREDENTIALS_PATH = (
    _firebase_default
    if _firebase_default.is_file()
    else (_firebase_adminsdk if _firebase_adminsdk is not None else _firebase_default)
)

# Push Notification Settings
PUSH_NOTIFICATION_SETTINGS = {
    'DEFAULT_SOUND': 'default',
    'DEFAULT_CHANNEL_ID': 'default',
    'MAX_RETRIES': 3,
    'BATCH_SIZE': 500,  # For bulk notifications
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_HEADERS = ['accept', 'accept-encoding', 'authorization', 'content-type', 'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with']
CORS_EXPOSE_HEADERS = ['authorization']
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# JWT settings (optional, for token lifetime)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Swagger/OpenAPI settings
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'DEFAULT_MODEL_RENDERING': 'example'
}

REDOC_SETTINGS = {
    'LAZY_RENDERING': False,
}

os.makedirs(MEDIA_ROOT / 'profile_images', exist_ok=True)
os.makedirs(MEDIA_ROOT / 'billboards', exist_ok=True)
os.makedirs(MEDIA_ROOT / 'chat_attachments', exist_ok=True)

# Billboard admin approval workflow (see billboards/views.py perform_create).
# True = new billboards are approved immediately (map/list visible without admin).
# False = new billboards stay pending until admin uses /api/billboards/pending/ + approval-status/.
BYPASS_BILLBOARD_APPROVAL = True

# Celery (view/lead tracking + push notifications in background)
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', '0') == '1'

# Channels Configuration removed
