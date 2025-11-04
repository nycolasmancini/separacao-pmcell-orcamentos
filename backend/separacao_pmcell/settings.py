# -*- coding: utf-8 -*-
"""
Django settings for separacao_pmcell project.
Fase 35: Configuração para Deploy em Produção
"""

import os
import sys
import urllib.parse
import socket
import logging
from pathlib import Path
from decouple import config, Csv
import dj_database_url

# Configure logging
logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# Em desenvolvimento, usa chave padrão. Em produção, DEVE vir do .env
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production-8#v7x$@p&m9z2k!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Hosts permitidos (separados por vírgula no .env)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,192.168.15.110,192.168.0.223,0.0.0.0', cast=Csv())

# CSRF Trusted Origins (para Railway e outros)
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'daphne',  # Fase 29: ASGI server (deve vir ANTES de django.contrib.staticfiles)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',  # Fase 29: WebSockets support
    'core',  # Nossa aplicação principal
]

# Fase 34 & 35: Detectar ambiente de testes
# Verifica se pytest está rodando, manage.py test, ou variável de ambiente
TESTING = (
    os.environ.get('DISABLE_DEBUG_TOOLBAR') == '1' or
    'pytest' in sys.modules or
    'py.test' in sys.modules or
    'test' in sys.argv  # Django manage.py test
)

# Fase 34: Debug toolbar (apenas em desenvolvimento, não em testes ou produção)
# Usa try/except para evitar erro se debug_toolbar não estiver instalado
DEBUG_TOOLBAR_ENABLED = False
if DEBUG and not TESTING:
    try:
        import debug_toolbar
        INSTALLED_APPS.insert(7, 'debug_toolbar')
        DEBUG_TOOLBAR_ENABLED = True
    except ImportError:
        pass

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Fase 35: Servir arquivos estáticos em produção
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.authentication.SessionTimeoutMiddleware',  # Middleware customizado - Fase 8
]

# Fase 34: Debug toolbar middleware (apenas se habilitado)
if DEBUG_TOOLBAR_ENABLED:
    MIDDLEWARE.insert(7, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'separacao_pmcell.urls'

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
                'core.context_processors.theme_colors',  # Context processor para cores do tema
            ],
        },
    },
]

WSGI_APPLICATION = 'separacao_pmcell.wsgi.application'

# Fase 29: ASGI application (para WebSockets)
ASGI_APPLICATION = 'separacao_pmcell.asgi.application'


# Database
# Fase 35: PostgreSQL em produção (via DATABASE_URL), SQLite em desenvolvimento
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Produção: usar PostgreSQL via DATABASE_URL (Railway fornece automaticamente)
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
else:
    # Desenvolvimento/Testes: usar SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
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


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Fase 35: Whitenoise - Servir arquivos estáticos em produção
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'core.Usuario'

# Session settings (8 horas)
SESSION_COOKIE_AGE = 28800  # 8 hours in seconds
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Cache configuration & Channel Layers
# Fase 35: Redis via REDIS_URL em produção, localhost em desenvolvimento
# Fase 36: Redis com fallback inteligente para ambientes sem Redis

def is_redis_available(redis_url_raw):
    """
    Valida se Redis URL contém hostname válido e resolvível.
    Retorna False se o hostname é um placeholder ou não pode ser resolvido.
    """
    parsed = urllib.parse.urlparse(redis_url_raw)
    hostname = parsed.hostname

    # Lista de placeholders comuns que Railway pode usar
    invalid_hostnames = ['host', 'password', 'username', 'port', 'your-redis-host']

    # Em produção, rejeita placeholders
    if not DEBUG and hostname and hostname.lower() in invalid_hostnames:
        logger.warning(f"Redis hostname '{hostname}' appears to be a placeholder - using fallback cache")
        return False

    # Em desenvolvimento, aceita localhost e 127.0.0.1
    if hostname in ['127.0.0.1', 'localhost', None]:
        # Aceita em desenvolvimento, mas verifica disponibilidade em produção
        if not DEBUG:
            return False
        return True

    # Tenta resolver o hostname para verificar se é válido
    try:
        socket.gethostbyname(hostname)
        logger.info(f"Redis hostname '{hostname}' resolved successfully")
        return True
    except (socket.gaierror, socket.herror, OSError) as e:
        logger.warning(f"Cannot resolve Redis hostname '{hostname}': {e} - using fallback cache")
        return False

# Parse seguro da REDIS_URL para evitar erros com placeholders
REDIS_URL_RAW = config('REDIS_URL', default='redis://127.0.0.1:6379/1')

# Parse do REDIS_URL para extrair componentes
redis_url_parsed = urllib.parse.urlparse(REDIS_URL_RAW)
redis_host = redis_url_parsed.hostname or '127.0.0.1'
redis_password = redis_url_parsed.password or None
redis_db = redis_url_parsed.path.lstrip('/') or '1'

# Tratamento robusto da porta para evitar erro com placeholders como 'port'
try:
    redis_port = int(redis_url_parsed.port) if redis_url_parsed.port else 6379
except (ValueError, TypeError):
    # Se a porta não puder ser convertida (ex: placeholder 'port'), usa padrão
    redis_port = 6379

# Reconstrói uma REDIS_URL válida e segura
if redis_password:
    REDIS_URL = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
else:
    REDIS_URL = f"redis://{redis_host}:{redis_port}/{redis_db}"

# Configuração do cache com fallback inteligente
USE_REDIS_CACHE = is_redis_available(REDIS_URL_RAW)

if USE_REDIS_CACHE:
    # Usa Redis quando disponível
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'KEY_PREFIX': 'separacao_pmcell',
            'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
        }
    }
    logger.info(f"✓ Using Redis cache backend: {redis_host}:{redis_port}")
else:
    # Fallback para cache local (desenvolvimento ou produção sem Redis)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'separacao_pmcell_cache',
            'OPTIONS': {
                'MAX_ENTRIES': 1000
            }
        }
    }
    logger.warning("⚠ Using local memory cache backend (Redis not available)")

# Fase 29: Channel Layers (Redis para WebSockets) com fallback
if USE_REDIS_CACHE:
    # Usa Redis para WebSockets quando disponível
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(redis_host, redis_port)],
            },
        },
    }
    logger.info("✓ Using Redis channel layer for WebSockets")
else:
    # Fallback para InMemory (apenas desenvolvimento/single-server)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
    logger.warning("⚠ Using in-memory channel layer (WebSockets work only on single server)")

# Fase 34: Django Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Configurações adicionais do Debug Toolbar (apenas se habilitado)
if DEBUG_TOOLBAR_ENABLED:
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    }
