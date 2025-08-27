# multi_tenant_shop/celery.py
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multi_tenant_shop.settings')

app = Celery('multi_tenant_shop')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()