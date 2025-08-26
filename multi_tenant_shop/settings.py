# multi_tenant_shop/settings.py

# ==============================================================================
# CORE DJANGO IMPORTS AND PATH CONFIGURATION
# ==============================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

import socket

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

# ==============================================================================
# CORE DJANGO SETTINGS
# ==============================================================================

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = True
ALLOWED_HOSTS = ['*'] # We use '*' for local development convenience. We'll make this more secure later.

# ==============================================================================
# MULTI-TENANCY CONFIGURATION (django-tenants)
# This is the brain of our multi-tenant architecture.
# ==============================================================================

# --- DATABASE ROUTER ---
# This tells Django to use the TenantSyncRouter, which is essential for
# directing database queries to the correct tenant schema.
DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

# --- MIDDLEWARE ---
# The TenantMainMiddleware must be the first middleware.
# It inspects the incoming request's hostname (e.g., 'store1.localhost')
# to determine the correct tenant and activates its schema for the entire request lifecycle.
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# --- SHARED AND TENANT APPS ---
# Here, we separate our Django apps into two categories:
# SHARED_APPS: These live in the 'public' schema and are shared by all tenants.
#              This includes the django-tenants app itself and the app that
#              defines our Tenant model (which we will create and name 'store').
SHARED_APPS = [
    'django_tenants',
    'store',  # Our app for managing tenants and later, products.
    'store_management',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',

    'crispy_forms',
    'crispy_bootstrap5',
]

# TENANT_APPS: These apps will have their tables created in EACH tenant's schema.
#              For example, each store will have its own set of products and orders.
#              Right now, we only list the essential Django apps that each tenant needs.
TENANT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Any other tenant-specific apps will be added here.

    'django_filters',
    'django_elasticsearch_dsl',
    'rest_framework',
]

# The final INSTALLED_APPS is a combination of both lists.
# The 'set' is used to remove duplicates.
INSTALLED_APPS = list(set(SHARED_APPS + TENANT_APPS))

# ==============================================================================
# STANDARD DJANGO CONFIGURATION (Continues)
# ==============================================================================

ROOT_URLCONF = 'multi_tenant_shop.urls'

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
                'store.context_processors.tenant_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'multi_tenant_shop.wsgi.application'

# --- DATABASE CONFIGURATION ---
DATABASES = {
    'default': {
        # We specify the postgresql_backend engine provided by django-tenants
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
    }
}

# ==============================================================================
# CACHING CONFIGURATION
# ==============================================================================
CACHES = {
    "default": {
        # Use the django-redis backend.
        "BACKEND": "django_redis.cache.RedisCache",
        # Connect to the 'redis' service defined in docker-compose.yml on the default port.
        # The '/1' specifies which Redis database to use (Redis can have multiple).
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- STATIC FILES ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# --- DEFAULT PRIMARY KEY ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================================================
# MULTI-TENANCY MODEL DEFINITIONS (django-tenants)
# ==============================================================================

# --- TENANT MODEL DEFINITION ---
# Here, we explicitly tell django-tenants which models in our project
# should be used for defining Tenants and their Domains.
# The format is 'app_label.ModelName'.
TENANT_MODEL = "store.Tenant"
TENANT_DOMAIN_MODEL = "store.Domain"

AUTH_USER_MODEL = 'store.User'

CART_SESSION_ID = 'cart'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ==============================================================================
# ELASTICSEARCH CONFIGURATION
# ==============================================================================
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': f"http://{os.getenv('ELASTICSEARCH_HOST')}:9200",
    },
}

# ==============================================================================
# DJANGO REST FRAMEWORK (DRF) CONFIGURATION
# ==============================================================================
REST_FRAMEWORK = {
    # This sets the default permission policy for all API views.
    # 'IsAuthenticatedOrReadOnly' allows any user (anonymous or logged in) to view the data (GET requests),
    # but requires the user to be authenticated for any write actions (POST, PUT, PATCH, DELETE).
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    # This defines the methods DRF will use to try to authenticate a user.
    # 'SessionAuthentication' is used for the Browsable API (it uses Django's login session).
    # 'TokenAuthentication' will be used later for mobile apps or other services.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework.authentication.TokenAuthentication', # We will enable this later
    ],
}

STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')

# This logic dynamically finds the host's IP address within the Docker network
# and adds it to INTERNAL_IPS, allowing the Debug Toolbar to appear.
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1"]