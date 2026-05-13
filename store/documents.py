# store/documents.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import ProductVariant

@registry.register_document
class ProductVariantDocument(Document):
    product_name = fields.TextField(
        attr='product.name',
        fields={'raw': fields.KeywordField()}
    )
    color = fields.TextField(
        fields={'raw': fields.KeywordField()}
    )

    # --- ADD THIS NEW FIELD ---
    # We need the product's slug to create correct links in the search results.
    # A 'KeywordField' is good for exact-match data like a slug.
    product_slug = fields.KeywordField(attr='product.slug')

    # Add tenant info for global search
    tenant_name = fields.KeywordField()
    tenant_domain = fields.KeywordField()

    def prepare_tenant_name(self, instance):
        # pyrefly: ignore [missing-import]
        from django.db import connection
        from store.models import Tenant
        tenant = getattr(connection, 'tenant', None)
        if not tenant or tenant.schema_name == 'public':
            return 'Unknown'
            
        if not hasattr(tenant, 'name'):
            real_tenant = Tenant.objects.filter(schema_name=tenant.schema_name).first()
            return real_tenant.name if real_tenant else 'Unknown'
        return tenant.name

    def prepare_tenant_domain(self, instance):
        from django.db import connection
        from store.models import Tenant
        tenant = getattr(connection, 'tenant', None)
        if not tenant or tenant.schema_name == 'public':
            return 'localhost'
            
        real_tenant = tenant
        if not hasattr(tenant, 'domains'):
            real_tenant = Tenant.objects.filter(schema_name=tenant.schema_name).first()
            
        if real_tenant and hasattr(real_tenant, 'domains') and real_tenant.domains.exists():
            return real_tenant.domains.first().domain
        return 'localhost'

    class Index:
        name = 'product_variants'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = ProductVariant
        fields = ['sku', 'sale_price', 'size', 'is_active']
