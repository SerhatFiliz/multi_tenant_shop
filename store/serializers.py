# store/serializers.py

"""
This file defines the Serializers for the 'store' application.
Serializers in Django REST Framework are responsible for converting complex data types,
such as Django model instances, into native Python datatypes that can then be
easily rendered into JSON, XML, or other content types. They also handle the
reverse process: validating and parsing incoming data back into complex types.
Essentially, they are the "translators" between our database models and the API representation.
"""

from rest_framework import serializers
from .models import Category, Product, ProductVariant

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.
    """
    class Meta:
        model = Category
        # Defines the fields to be included in the API output.
        fields = ['id', 'name', 'slug']

class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProductVariant model.
    """
    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'color', 'size', 'sale_price', 'stock_quantity']

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model.
    This serializer includes its related variants using a nested serializer,
    demonstrating how to represent relationships in an API.
    """
    # 'variants' is the 'related_name' from the ProductVariant model's ForeignKey.
    # 'many=True' indicates that a product can have multiple variants.
    # 'read_only=True' means this nested data can be viewed but not updated through this specific serializer.
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    # We are also nesting the CategorySerializer to show category details, not just its ID.
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'variants']