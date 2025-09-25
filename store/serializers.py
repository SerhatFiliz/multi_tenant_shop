# multi_tenant_shop/store/serializers.py

"""
This file defines the Serializers for the 'store' application.
Serializers in Django REST Framework are responsible for converting complex data types,
such as Django model instances, into native Python datatypes that can then be
easily rendered into JSON, XML, or other content types. They also handle the
reverse process: validating and parsing incoming data back into complex types.
Essentially, they are the "translators" between our database models and the API representation.
"""

from rest_framework import serializers
from .models import User, Category, Product, ProductVariant, Order, OrderItem, Address, Review

# ==============================================================================
# PRODUCT CATALOG SERIALIZERS
# These serializers are for handling product and category data.
# ==============================================================================

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

# ==============================================================================
# NEW SERIALIZERS
# These are the serializers we need for user, order, and review endpoints.
# ==============================================================================

class UserSerializer(serializers.ModelSerializer):
    """
    Serializes the User model.
    This serializer is used to represent the authenticated user's profile data.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        # We make the email field read-only to prevent it from being changed
        # through this serializer. This is a security measure.
        read_only_fields = ('email',)


class AddressSerializer(serializers.ModelSerializer):
    """
    Serializes the Address model.
    """
    class Meta:
        model = Address
        fields = (
            'id', 'address_title', 'full_name', 'phone_number',
            'address_line_1', 'city', 'postal_code', 'is_default'
        )


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializes an OrderItem, including the details of the product variant.
    """
    # Use a custom serializer to show details of the ordered product variant.
    product_variant = ProductVariantSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('product_variant', 'quantity', 'price')


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializes an Order, including all its items.
    """
    # Use the OrderItemSerializer to list all items within the order.
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'order_date', 'total_amount', 'status', 'items')


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializes a Review, allowing users to submit new reviews.
    """
    # Use the user's username for better readability in the API response.
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'user', 'rating', 'comment', 'created_at')
        # We make the user and created_at fields read-only as they are set by the server.
        read_only_fields = ('user', 'created_at',)