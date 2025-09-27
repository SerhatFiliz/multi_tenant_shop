import os
import django
from django.conf import settings

# Django ayarlarını yapılandırma
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multi_tenant_shop.settings')
django.setup()

from store.models import Tenant, Domain
from django_tenants.utils import schema_context
from django.core.management import call_command

# Tenant oluştur
tenant = Tenant(
    schema_name='inciboncuk',
    name='İnci Boncuk Tuhafiye',
    is_approved=True,
)
tenant.save()

# Tenant için migrations uygula (Bu satıra gerek yoktu, otomatik çalışır)
# with schema_context(tenant.schema_name):
#     call_command('migrate')

# Domain ekle
domain = Domain()
domain.domain = 'inciboncuk.localhost'
domain.tenant = tenant
domain.is_primary = True
domain.save()

print("Tenant ve domain başarıyla oluşturuldu!")