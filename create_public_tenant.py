import os
import django
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multi_tenant_shop.settings')
django.setup()

from store.models import Tenant, Domain

def create_public_tenant():
    print("[INIT] Checking for Public Tenant...")
    
    # 1. Create the 'public' tenant if it doesn't exist
    tenant, created = Tenant.objects.get_or_create(
        schema_name='public',
        defaults={
            'name': 'Master System',
            'is_approved': True
        }
    )
    
    if created:
        print(f"[OK]   Created Public Tenant: {tenant.name}")
    else:
        print(f"[INFO] Public Tenant already exists.")

    # 2. Add domains to the public tenant
    domains = ['127.0.0.1', 'localhost']
    for domain_name in domains:
        domain, dom_created = Domain.objects.get_or_create(
            domain=domain_name,
            defaults={'tenant': tenant, 'is_primary': True if domain_name == '127.0.0.1' else False}
        )
        if dom_created:
            print(f"[OK]   Added domain: {domain_name}")
        else:
            print(f"[INFO] Domain already exists: {domain_name}")

if __name__ == "__main__":
    try:
        create_public_tenant()
    except Exception as e:
        print(f"[ERR]  Failed to initialize public tenant: {e}")
