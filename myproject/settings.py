"""
Django settings for myproject project.

Для настройки переменных окружения используйте файлы:
- .env (основные настройки)
- .env.local (локальные переопределения)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Загрузка переменных окружения
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.local")


# =============================================================================
# ОСНОВНЫЕ НАСТРОЙКИ
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
DEBUG = os.getenv("DEBUG", "").lower() in {"1", "true", "yes"}

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-dev"
    else:
        raise ValueError("SECRET_KEY env var is required when DEBUG=False")

# Хосты, на которых разрешено обслуживание приложения
allowed_hosts_env = os.getenv("ALLOWED_HOSTS", "")
if allowed_hosts_env:
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(",") if host.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
else:
    ALLOWED_HOSTS = []


# =============================================================================
# ПРИЛОЖЕНИЯ
# =============================================================================

INSTALLED_APPS = [
    # Django встроенные приложения
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Локальные приложения
    'myapp',
]


# =============================================================================
# ПРОСЛОЙКИ (MIDDLEWARE)
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Для обслуживания статических файлов
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'


# =============================================================================
# ШАБЛОНЫ
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # глобальные шаблоны
        ],
        'APP_DIRS': True,  # ИСКАТЬ ШАБЛОНЫ В ПРИЛОЖЕНИЯХ
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


# =============================================================================
# КЭШИРОВАНИЕ
# =============================================================================

# ОТКЛЮЧАЕМ КЭШ В РАЗРАБОТКЕ
if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }


# =============================================================================
# БАЗА ДАННЫХ
# =============================================================================

# Database
if os.getenv("USE_SQLITE") == "True":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    print("Use SQLITE")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT"),
        }
    }
    print("Use PostgreSQL")


# =============================================================================
# ВАЛИДАЦИЯ ПАРОЛЕЙ
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =============================================================================
# ИНТЕРНАЦИОНАЛИЗАЦИЯ
# =============================================================================

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True


# =============================================================================
# СТАТИЧЕСКИЕ ФАЙЛЫ
# =============================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# =============================================================================
# МЕДИА ФАЙЛЫ
# =============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# =============================================================================
# АВТОРИЗАЦИЯ
# =============================================================================

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/profile/'
LOGOUT_REDIRECT_URL = '/'


# =============================================================================
# БЕЗОПАСНОСТЬ
# =============================================================================

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# =============================================================================
# ОБРАБОТЧИКИ ОШИБОК
# =============================================================================

HANDLER404 = 'myproject.handler.handler404'
HANDLER500 = 'myproject.handler.handler500'
HANDLER403 = 'myproject.handler.handler403'
HANDLER400 = 'myproject.handler.handler400'


# =============================================================================
# ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
# =============================================================================

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
