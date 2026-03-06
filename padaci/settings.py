"""
PADACI – Sistema de Logística de Entrega
Django settings
"""
import os
from pathlib import Path

try:
    from decouple import config  # type: ignore
except Exception:
    # Fallback for hosting environments where python-decouple is not installed.
    def config(name, default=None, cast=str):
        value = os.getenv(name, default)
        if cast is bool and isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        if cast and value is not None and cast is not bool:
            try:
                return cast(value)
            except Exception:
                return default
        return value

try:
    import pymysql

    pymysql.install_as_MySQLdb()
except Exception:
    # If PyMySQL is unavailable but mysqlclient exists, Django can still work.
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────────────
# Fallback key avoids hard crash when environment variables are not loaded in hosting.
SECRET_KEY = config('SECRET_KEY', default='django-insecure-padaci-change-this-secret-key')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1').split(',')
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in config('CSRF_TRUSTED_ORIGINS', default='').split(',')
    if origin.strip()
]

# ── Apps ──────────────────────────────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY = [
    'crispy_forms',
    'crispy_bootstrap4',
    'rest_framework',
    'django_tables2',
    'django_filters',
    'import_export',
]

LOCAL_APPS = [
    'accounts',
    'clients',
    'companies',
    'deliveries',
    'history',
    'maps',
    'routes',
    'rendiciones',
    'dashboard',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY + LOCAL_APPS

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'padaci.middleware.ExceptionFileLoggingMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'padaci.urls'

# ── Templates ─────────────────────────────────────────────────────────────────
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

WSGI_APPLICATION = 'padaci.wsgi.application'

# ── Database – MySQL ──────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='padaci_db'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ── Auth ───────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ── Internationalización ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','
NUMBER_GROUPING = 3
FORMAT_MODULE_PATH = ['padaci.formats']

# ── Static & Media ────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Manifest storage can raise 500 if collectstatic output is stale/missing in shared hosting.
STATICFILES_STORAGE = config(
    'STATICFILES_STORAGE',
    default='whitenoise.storage.CompressedStaticFilesStorage',
)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Crispy Forms ──────────────────────────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# ── DRF ───────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# ── Tables2 ───────────────────────────────────────────────────────────────────
DJANGO_TABLES2_TEMPLATE = 'django_tables2/bootstrap4.html'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Hardening producción ─────────────────────────────────────────────────────
# Configurable proxy SSL header for shared hostings (cPanel/Passenger, Nginx, etc.).
_proxy_ssl_header_raw = config('SECURE_PROXY_SSL_HEADER', default='').strip()
if _proxy_ssl_header_raw:
    _parts = [p.strip() for p in _proxy_ssl_header_raw.split(',') if p.strip()]
    SECURE_PROXY_SSL_HEADER = (_parts[0], _parts[1]) if len(_parts) == 2 else None
else:
    SECURE_PROXY_SSL_HEADER = None

USE_X_FORWARDED_HOST = config('USE_X_FORWARDED_HOST', default=False, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Defaulting to False avoids redirect loops when proxy SSL headers are not configured.
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
