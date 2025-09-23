from store.models import Tenant, Domain
from django_tenants.utils import schema_context
from django.core.management import call_command

# Tenant oluştur
tenant = Tenant(
    schema_name='inci_boncuk_tuhafiye',
    name='İnci Boncuk Tuhafiye',
)
tenant.save()

# Tenant için migrations uygula
with schema_context(tenant.schema_name):
    call_command('migrate')

# Domain ekle
domain = Domain()
domain.domain = 'inciboncuk.localhost'
domain.tenant = tenant
domain.is_primary = True
domain.save()

print("Tenant ve domain başarıyla oluşturuldu!")
