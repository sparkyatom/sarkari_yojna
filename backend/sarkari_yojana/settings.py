"""
SarkariYojana Django Settings
"""
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SECURITY ───
SECRET_KEY = 'django-insecure-sarkari-yojana-change-this-in-production-2024'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# ─── APPS ───
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',   # FIX: required for JWT logout blacklisting
    'corsheaders',
    # Our apps
    'schemes',
    'users',
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',       # Must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sarkari_yojana.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

WSGI_APPLICATION = 'sarkari_yojana.wsgi.application'

# ─── DATABASE (MySQL) ───
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.mysql',
        'NAME':     'sarkari_yojana_db',
        'USER':     'syuser',
        'PASSWORD': 'SY@pass2024',
        'HOST':     'localhost',
        'PORT':     '3306',
        'OPTIONS':  {
            'charset': 'utf8mb4',
            # FIX: removed STRICT_TRANS_TABLES from sql_mode override so MySQL's
            # own default mode is used — avoids conflicts with TEXT column handling.
            'init_command': "SET sql_mode='NO_ENGINE_SUBSTITUTION'",
        },
    }
}

# ─── CUSTOM USER MODEL ───
AUTH_USER_MODEL = 'users.UserProfile'

# ─── REST FRAMEWORK ───
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# ─── JWT SETTINGS ───
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':    timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME':   timedelta(days=30),
    'ROTATE_REFRESH_TOKENS':    True,
    'BLACKLIST_AFTER_ROTATION': True,   # requires token_blacklist in INSTALLED_APPS
    'AUTH_HEADER_TYPES':        ('Bearer',),
}

# ─── CORS (allow frontend) ───
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5500',
    'http://127.0.0.1:5500',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True

# ─── STATIC & MEDIA ───
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

# ─── LANGUAGE / TIME ───
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── PASSWORD VALIDATORS ───
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
]
