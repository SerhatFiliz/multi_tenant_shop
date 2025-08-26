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
    This version handles nested reading and simple writing of relationships.
    """
    # For GET requests (reading data), show the full nested Category object.
    category = CategorySerializer(read_only=True)
    # For POST/PUT requests (writing data), expect only the category's primary key (ID).
    # 'write_only=True' means this field is used for input, but not shown in the output.
    # 'queryset' is needed for validation to ensure the provided ID is valid.
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )
    
    # The nested variants representation remains the same (read-only).
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        # Add 'category_id' to the list of fields.
        fields = ['id', 'name', 'slug', 'description', 'category', 'category_id', 'variants']