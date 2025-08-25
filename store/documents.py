# store/documents.py

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from .models import ProductVariant

@registry.register_document
class ProductVariantDocument(Document):
    """
    This class defines the Elasticsearch document for our ProductVariant model.
    It specifies which fields from the model should be indexed and how.
    """
    
    # We create a 'TextField' for product name to enable full-text search.
    # We access the related Product model's name via 'product.name'.
    product_name = fields.TextField(
        attr='product.name',
        fields={
            'raw': fields.KeywordField(),
        }
    )
    
    # We create a 'TextField' for color, also for full-text search.
    color = fields.TextField(
        fields={
            'raw': fields.KeywordField(),
        }
    )

    class Index:
        # Name of the Elasticsearch index
        name = 'product_variants'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = ProductVariant # The model associated with this document
        
        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'sku',
            'sale_price',
            'size',
            'is_active',
        ]