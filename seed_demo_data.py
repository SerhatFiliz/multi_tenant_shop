import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multi_tenant_shop.settings')
django.setup()

from store.models import Product, ProductVariant, Category, User, Order, OrderItem, Address
from django.utils.text import slugify

def seed_database():
    print("[INIT] Seeding the Grand Simulation Dataset (Nexus Kitchen)...")
    
    # 1. Create a dummy admin/user if not exists
    user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@nexus.com'})
    user.set_password('admin123')
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    # Create Address for user
    address, _ = Address.objects.get_or_create(user=user, defaults={
        'address_title': 'Work Address',
        'full_name': 'Admin User',
        'phone_number': '5551234567',
        'address_line_1': '123 Innovation Drive',
        'city': 'Tech City',
        'postal_code': '10001'
    })
    
    # 2. Categories
    cat_kitchen, _ = Category.objects.get_or_create(name='Smart Kitchen', slug='smart-kitchen')
    cat_appliances, _ = Category.objects.get_or_create(name='Premium Appliances', slug='premium-appliances')
    cat_accessories, _ = Category.objects.get_or_create(name='Accessories', slug='accessories')
    
    # 3. Products
    products_data = [
        # Anomaly Products
        ("Pro-Mixer 5000", cat_appliances, "Ultimate baking companion", 499.99, 2, "mixer-5000"), # Stock < 3
        ("Smart Oven", cat_appliances, "AI-powered baking oven", 899.99, 1, "smart-oven"), # Stock < 3
        # Other premium products
        ("Nexus Coffee Maker", cat_kitchen, "Barista level coffee at home", 299.99, 45, "coffee-maker"),
        ("Aero-Fryer Pro", cat_kitchen, "Healthy frying with air", 199.99, 30, "aero-fryer"),
        ("Digital Food Scale", cat_accessories, "Precision measuring", 49.99, 120, "food-scale"),
        ("Smart Refrigerator", cat_appliances, "Family hub fridge", 2499.99, 15, "smart-fridge"),
        ("Chef's Knife Set", cat_accessories, "Damascus steel knife set", 149.99, 50, "knife-set"),
        ("Automatic Pan Stirrer", cat_accessories, "Hands-free cooking", 39.99, 80, "pan-stirrer"),
        ("Sous Vide Precision Cooker", cat_kitchen, "Perfect temp cooking", 129.99, 25, "sous-vide"),
        ("Electric Kettle Plus", cat_kitchen, "Boils in 60s", 89.99, 60, "electric-kettle"),
        ("Smart Blender Max", cat_appliances, "High power blending", 249.99, 40, "blender-max"),
        ("Silicone Utensil Set", cat_accessories, "Heat resistant tools", 29.99, 150, "utensil-set"),
        ("Induction Cooktop", cat_appliances, "Portable induction burner", 199.99, 20, "induction-cooktop"),
        ("Vacuum Sealer", cat_kitchen, "Preserve food longer", 79.99, 35, "vacuum-sealer"),
        ("Digital Meat Thermometer", cat_accessories, "Bluetooth connected temp", 59.99, 100, "meat-thermometer")
    ]
    
    variants = []
    for name, cat, desc, price, stock, sku in products_data:
        p, _ = Product.objects.get_or_create(name=name, category=cat, defaults={'slug': slugify(name), 'description': desc})
        pv, _ = ProductVariant.objects.get_or_create(product=p, sku=sku, defaults={'sale_price': price, 'stock_quantity': stock})
        variants.append(pv)
        
    # Generate 60+ orders over the last 30 days
    now = timezone.now()
    print("[INIT] Generating 60+ historical orders...")
    
    # Keep track of orders to avoid duplicates
    Order.objects.all().delete() # Clean slate for orders for fresh simulation
    
    for i in range(60):
        days_ago = random.randint(1, 30)
        order_date = now - timedelta(days=days_ago)
        
        o = Order.objects.create(
            user=user,
            shipping_address=address,
            total_amount=0,
            status='delivered',
            paid=True,
            order_date=order_date
        )
        
        # Add 1-3 random items
        total = 0
        for _ in range(random.randint(1, 3)):
            v = random.choice(variants)
            qty = random.randint(1, 2)
            OrderItem.objects.create(order=o, product_variant=v, price=v.sale_price, quantity=qty)
            total += v.sale_price * qty
            
        o.total_amount = total
        o.save()
        
    # SHIPPING ANOMALY: 3 orders with status 'Shipped' but Target Delivery Date in the past.
    print("[INIT] Creating 3 delayed shipped orders (Anomalies)...")
    for i in range(3):
        # We simulate delay by setting order_date 10 days ago, shipped, but not delivered.
        order_date = now - timedelta(days=10)
        o = Order.objects.create(
            user=user,
            shipping_address=address,
            total_amount=0,
            status='shipped',
            paid=True,
            order_date=order_date
        )
        v = random.choice(variants)
        qty = random.randint(1, 2)
        OrderItem.objects.create(order=o, product_variant=v, price=v.sale_price, quantity=qty)
        o.total_amount = v.sale_price * qty
        o.save()

    # TASK LIST: 5 'Pending' orders for 'Today'
    print("[INIT] Creating 5 pending orders for today's warehouse task list...")
    for i in range(5):
        o = Order.objects.create(
            user=user,
            shipping_address=address,
            total_amount=0,
            status='processing',
            paid=True,
            order_date=now # Today
        )
        v = random.choice(variants)
        qty = random.randint(1, 2)
        OrderItem.objects.create(order=o, product_variant=v, price=v.sale_price, quantity=qty)
        o.total_amount = v.sale_price * qty
        o.save()

    print("[OK]   Grand Simulation Dataset initialized successfully.")
    
if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        print(f"[ERR]  Failed to seed data: {e}")
