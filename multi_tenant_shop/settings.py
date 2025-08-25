# multi_tenant_shop/settings.py

# ==============================================================================
# CORE DJANGO IMPORTS AND PATH CONFIGURATION
# ==============================================================================

import os
from pathlib import Path
from dotenv import load_dotenv

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
]

# --- SHARED AND TENANT APPS ---
# Here, we separate our Django apps into two categories:
# SHARED_APPS: These live in the 'public' schema and are shared by all tenants.
#              This includes the django-tenants app itself and the app that
#              defines our Tenant model (which we will create and name 'store').
SHARED_APPS = [
    'django_tenants',
    'store',  # Our app for managing tenants and later, products.

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

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