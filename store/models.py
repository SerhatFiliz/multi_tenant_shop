# store/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django_tenants.models import TenantMixin, DomainMixin
from django.conf import settings

# ==============================================================================
# MULTI-TENANCY CORE MODELS (SHARED)
# These models live in the 'public' schema and manage the tenants.
# ==============================================================================

class Tenant(TenantMixin):
    """
    This model represents a Tenant, which is a single store in our platform.
    It inherits from TenantMixin, providing the core multi-tenancy logic.
    """
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)

    # auto_create_schema is set to True so that as soon as a Tenant is created,
    # its database schema will be automatically created.
    auto_create_schema = True

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    """
    This model represents a domain name that maps to a specific Tenant.
    For example: 'inciboncuk.localhost' -> Tenant 'İnci Boncuk Tuhafiye'
    It inherits from DomainMixin.
    """
    def __str__(self):
        return f"{self.domain} -> {self.tenant.name}"

# ==============================================================================
# TENANT-SPECIFIC MODELS
# The tables for these models will be created in EACH tenant's schema.
# ==============================================================================

# --- User Management Models ---

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    We explicitly define the 'groups' and 'user_permissions' fields
    to add a unique 'related_name' and resolve the system check error E304.
    """
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        # This unique related_name is the solution to the clash.
        related_name="store_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        # This unique related_name is also a solution to the clash.
        related_name="store_user_permissions_set",
        related_query_name="user",
    )
    # We can add extra fields here later if we want.
    pass


class Address(models.Model):
    """
    Stores shipping addresses for users. A user can have multiple addresses.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    address_title = models.CharField(max_length=100, help_text="e.g., Home Address, Work Address")
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.user.username} - {self.address_title}"

# --- Product Catalog Models ---

class Category(models.Model):
    """
    Represents a product category, e.g., 'Beads', 'Threads'.
    Supports sub-categories.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    """
    Represents a main product, which can have multiple variations.
    e.g., '10mm Crystal Bead'
    """
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    """
    Represents a specific variation of a Product.
    e.g., '10mm Crystal Bead, Color: Sapphire Blue'
    This model holds the actual stock and price information.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} ({self.color or ''} {self.size or ''}) - SKU: {self.sku}"

# --- Order Management Models ---

class Order(models.Model):
    """
    Represents a customer's order, containing one or more OrderItems.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Order #{self.id} by {self.user.username if self.user else 'Guest'}"

class OrderItem(models.Model):
    """
    Represents a single item within an Order.
    Connects an Order to a specific ProductVariant.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price at the time of purchase")

    def __str__(self):
        return f"{self.quantity} x {self.product_variant.product.name} in Order #{self.order.id}"

# --- User Interaction Models ---

class Review(models.Model):
    """
    Represents a review and rating left by a user for a product.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(help_text="Rating from 1 to 5")
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"


# --- Inventory & Profitability Models (for future use) ---
# These models lay the groundwork for tracking purchase costs and calculating profit.

class Supplier(models.Model):
    """
    Represents a supplier from whom we purchase products.
    """
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    """
    Represents a purchase order we place with a Supplier.
    """
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    order_date = models.DateTimeField(auto_now_add=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Purchase Order from {self.supplier.name} on {self.order_date.date()}"

class PurchaseOrderItem(models.Model):
    """
    Represents a single item within a PurchaseOrder.
    This is the KEY for profit calculation, as it stores the purchase_price.
    """
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost per unit")

    def __str__(self):
        return f"{self.quantity} x {self.product_variant.sku} @ {self.purchase_price}"