# store/admin.py

# ==============================================================================
# DJANGO ADMIN CONFIGURATION FOR THE 'STORE' APP
# ==============================================================================
# This file is the control center for how your models are displayed and managed
# in the Django administration panel. By creating custom classes that inherit
# from `admin.ModelAdmin`, we can unlock powerful features like custom list
# displays, search functionality, filters, and much more.
# ==============================================================================

from django.contrib import admin
from .models import (
    Tenant, Domain, User, Address, Category, Product, ProductVariant,
    Order, OrderItem, Review, Supplier, PurchaseOrder, PurchaseOrderItem
)

# ==============================================================================
# INLINE MODELADMIN CLASSES
# ==============================================================================
# Inlines are a powerful feature that allow you to edit models on the same page
# as a parent model. Here, we want to manage ProductVariants directly from the
# Product page, creating a much better user experience.

class ProductVariantInline(admin.TabularInline):
    """
    Defines the inline editor for ProductVariant models.
    'TabularInline' provides a compact, table-based layout for editing.
    This will be "plugged into" the ProductAdmin class below.
    """
    model = ProductVariant  # Specifies which model this inline is for.
    extra = 1  # Provides 1 extra empty form for adding a new variant by default.

# ==============================================================================
# MAIN MODELADMIN CLASSES
# ==============================================================================
# These classes customize the main admin pages for our most important models.
# The '@admin.register()' decorator is a clean, modern way to register a model
# with its custom ModelAdmin class. It's equivalent to writing
# `admin.site.register(Product, ProductAdmin)` at the end of the file.

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Product model.
    """
    # `list_display` controls which fields are shown in the main list view of all products.
    # It turns the simple list into a powerful, data-rich table.
    list_display = ('name', 'category', 'is_active', 'created_at')

    # `list_filter` adds a sidebar that allows you to filter the results.
    # You can filter by fields on the model itself, or even traverse relationships
    # using the '__' (double underscore) syntax.
    list_filter = ('category', 'is_active')

    # `search_fields` adds a search bar at the top of the list view.
    # It will search the specified text fields for your query.
    search_fields = ('name', 'description')

    # `prepopulated_fields` is a magical feature. It uses JavaScript to automatically
    # fill the 'slug' field based on the text you type into the 'name' field,
    # ensuring your URLs are clean and SEO-friendly.
    prepopulated_fields = {'slug': ('name',)}

    # `inlines` is where we plug in our inline classes.
    # This line tells Django: "When someone is editing a Product, also show
    # the ProductVariantInline editor at the bottom of the page."
    inlines = [ProductVariantInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the ProductVariant model.
    """
    # `__str__` refers to the output of the model's __str__ method.
    # 'product__category' shows how to display a field from a related model.
    list_display = ('__str__', 'sku', 'sale_price', 'stock_quantity', 'is_active')
    list_filter = ('is_active', 'product__category')
    search_fields = ('sku', 'product__name')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Category model.
    """
    list_display = ('name', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Order model.
    """
    # 'id' is useful for quickly identifying orders.
    list_display = ('id', 'user', 'status', 'total_amount', 'order_date')
    list_filter = ('status', 'order_date')
    # 'user__username' allows searching for orders by the customer's username.
    search_fields = ('user__username', 'id')

# ==============================================================================
# SIMPLE REGISTRATIONS
# ==============================================================================
# For models that don't need a highly customized admin interface yet,
# we can register them directly. They will use Django's default admin options.
# This is a quick way to make them visible and manageable.

# Multi-Tenancy Core Models
admin.site.register(Tenant)
admin.site.register(Domain)

# User Management Models
admin.site.register(User)
admin.site.register(Address)

# Other Models
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Supplier)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)