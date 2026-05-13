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
    Order, OrderItem, Review, Supplier, PurchaseOrder, PurchaseOrderItem,
    TenantInvitation, ProductPriceHistory, ExchangeRateCache, StoreSettings, Message
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
    model = ProductVariant
    extra = 1

# ==============================================================================
# MAIN MODELADMIN CLASSES
# ==============================================================================
# These classes customize the main admin pages for our most important models.
# The '@admin.register()' decorator is a clean, modern way to register a model
# with its custom ModelAdmin class. It's equivalent to writing
# `admin.site.register(Product, ProductAdmin)` at the end of the file.

# Admin class for the Tenant model.
@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Tenant model.
    """
    list_display = ['schema_name', 'name', 'is_approved', 'created_on']
    list_filter = ['is_approved']
    search_fields = ['name', 'schema_name']


# Admin class for the Product model.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Product model.
    """
    list_display = ('name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductVariantInline]

# Admin class for the ProductVariant model.
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the ProductVariant model.
    """
    list_display = ('__str__', 'sku', 'sale_price', 'stock_quantity', 'is_active')
    list_filter = ('is_active', 'product__category')
    search_fields = ('sku', 'product__name')

# Admin class for the Category model.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Category model.
    """
    list_display = ('name', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

# Admin class for the Order model.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Order model.
    """
    list_display = ('id', 'user', 'status', 'total_amount', 'order_date')
    list_filter = ('status', 'order_date')
    search_fields = ('user__username', 'id')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "sender", "receiver", "sentiment", "is_high_priority", "is_read", "timestamp")
    list_filter = ("store", "sentiment", "is_high_priority", "is_read", "timestamp")
    search_fields = ("sender__username", "receiver__username", "content")

# ==============================================================================
# SIMPLE REGISTRATIONS
# ==============================================================================
# For models that don't need a highly customized admin interface yet,
# we can register them directly. They will use Django's default admin options.
# This is a quick way to make them visible and manageable.
admin.site.register(Domain)
admin.site.register(User)
admin.site.register(Address)
admin.site.register(OrderItem)
admin.site.register(Review)
admin.site.register(Supplier)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)
admin.site.register(TenantInvitation)
admin.site.register(ProductPriceHistory)
admin.site.register(ExchangeRateCache)
admin.site.register(StoreSettings)
