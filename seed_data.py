import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multi_tenant_shop.settings')
django.setup()

from store.models import Product, ProductVariant, Category, User, Order, OrderItem
from django.utils.text import slugify

def seed_database():
    print("[INIT] Seeding dummy data for AI analysis...")
    
    # 1. Create a dummy admin/user if not exists
    user, _ = User.objects.get_or_create(username='admin', email='admin@example.com')
    
    # 2. Categories
    cat_kitchen, _ = Category.objects.get_or_create(name='Kitchen', slug='kitchen')
    cat_electronics, _ = Category.objects.get_or_create(name='Electronics', slug='electronics')
    
    # 3. Products
    products_data = [
        ("Professional Stand Mixer X", cat_kitchen, "High-end kitchen mixer", 299.99, 15, "mixer-x"),
        ("Smart Blender Pro", cat_kitchen, "Smart blender with AI", 149.99, 45, "blender-pro"),
        ("Ultra Toaster 3000", cat_kitchen, "Toast your bread smartly", 49.99, 120, "toaster-3000"),
        ("Developer Laptop Elite", cat_electronics, "High performance laptop", 1999.99, 5, "laptop-elite"),
        ("Wireless Noise-Canceling Headphones", cat_electronics, "Silence the world", 249.99, 30, "headphones-nc")
    ]
    
    for name, cat, desc, price, stock, sku in products_data:
        p, _ = Product.objects.get_or_create(name=name, category=cat, defaults={'slug': slugify(name), 'description': desc})
        ProductVariant.objects.get_or_create(product=p, sku=sku, defaults={'sale_price': price, 'stock_quantity': stock})
        
    print("[OK]   Database seeded with 5 products.")
    
if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        print(f"[ERR]  Failed to seed data: {e}")
