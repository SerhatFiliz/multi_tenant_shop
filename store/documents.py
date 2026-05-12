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
        # The schema_name is typically available via connection.tenant, but 
        # since indexing might happen in background, let's look up the tenant.
        from django.db import connection
        tenant = getattr(connection, 'tenant', None)
        return tenant.name if tenant and tenant.schema_name != 'public' else 'Unknown'

    def prepare_tenant_domain(self, instance):
        from django.db import connection
        tenant = getattr(connection, 'tenant', None)
        if tenant and tenant.schema_name != 'public' and tenant.domains.exists():
            return tenant.domains.first().domain
        return 'localhost'

    class Index:
        name = 'product_variants'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = ProductVariant
        fields = ['sku', 'sale_price', 'size', 'is_active']