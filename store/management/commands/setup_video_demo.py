import uuid
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from store.models import Tenant, Domain, Product, ProductVariant, Category, Order, OrderItem, Address

User = get_user_model()

class Command(BaseCommand):
    help = 'Flawless database seeder for the Split-Screen Video Demo.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting Video Demo Seed Script..."))
        
        # 1. TENANT CONTEXT
        tenant, created = Tenant.objects.get_or_create(
            schema_name='nexus',
            defaults={
                'name': 'Nexus Demo Store',
                'is_approved': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Tenant: Nexus Demo Store (schema: nexus)'))
        else:
            self.stdout.write(self.style.SUCCESS('Found Tenant: Nexus Demo Store (schema: nexus)'))

        domain, dom_created = Domain.objects.get_or_create(
            domain='nexus.localhost',
            defaults={'tenant': tenant, 'is_primary': True}
        )
        if dom_created:
            self.stdout.write(self.style.SUCCESS('Created Domain: nexus.localhost'))
        else:
            self.stdout.write(self.style.SUCCESS('Found Domain: nexus.localhost'))

        # Switch to the tenant schema explicitly
        with schema_context(tenant.schema_name):
            self.stdout.write(self.style.WARNING(f"\nSwitched to schema: {tenant.schema_name}"))

            # 2. CREATE DEDICATED ACCOUNTS
            owner_email = 'owner@nexus.com'
            if not User.objects.filter(username=owner_email).exists() and not User.objects.filter(email=owner_email).exists():
                owner = User.objects.create_superuser(
                    username=owner_email,
                    email=owner_email,
                    password='admin123'
                )
                owner.is_staff = True
                owner.is_superuser = True
                owner.save()
                self.stdout.write(self.style.SUCCESS(f"Created Store Owner: {owner_email}"))
            else:
                self.stdout.write(self.style.WARNING(f"Store Owner already exists: {owner_email}"))

            customer_email = 'customer@demo.com'
            if not User.objects.filter(username=customer_email).exists() and not User.objects.filter(email=customer_email).exists():
                customer = User.objects.create_user(
                    username=customer_email,
                    email=customer_email,
                    password='admin123'
                )
                self.stdout.write(self.style.SUCCESS(f"Created Customer: {customer_email}"))
            else:
                customer = User.objects.get(email=customer_email)
                self.stdout.write(self.style.WARNING(f"Customer already exists: {customer_email}"))

            # 3. CLEAN & SEED CATALOG
            self.stdout.write(self.style.WARNING("\nCleaning existing catalog to prevent duplicates..."))
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            ProductVariant.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()

            category = Category.objects.create(name="Smart Tech", slug="smart-tech")
            
            products_to_create = [
                {"name": "Pro-Mixer 5000", "price": 499.99, "cost": 200.00, "stock": 10},
                {"name": "Smart Oven X", "price": 899.99, "cost": 450.00, "stock": 10},
                {"name": "AI Coffee Maker", "price": 299.99, "cost": 100.00, "stock": 10},
                {"name": "Industrial Blender", "price": 1299.99, "cost": 600.00, "stock": 10},
                {"name": "Digital Scale", "price": 49.99, "cost": 15.00, "stock": 10},
            ]

            variants = []
            for item in products_to_create:
                slug = item["name"].lower().replace(" ", "-") + "-" + uuid.uuid4().hex[:6]
                
                prod = Product.objects.create(
                    category=category,
                    name=item["name"],
                    slug=slug,
                    description=f"High performance {item['name']} engineered for B2B operations.",
                    is_active=True
                )
                
                var = ProductVariant.objects.create(
                    product=prod,
                    sku=f"SKU-{uuid.uuid4().hex[:8].upper()}",
                    sale_price=item["price"],
                    cost_price=item["cost"],
                    stock_quantity=item["stock"],
                    is_active=True
                )
                variants.append(var)
                self.stdout.write(self.style.SUCCESS(f"Created Product & Variant: {prod.name} (SKU: {var.sku})"))

            # 4. SEED ORDERS (For the AI Dashboard to analyze)
            self.stdout.write(self.style.WARNING("\nSeeding Mock Orders..."))
            
            address, _ = Address.objects.get_or_create(
                user=customer,
                address_title="Main Warehouse",
                defaults={
                    "full_name": "Demo Customer",
                    "phone_number": "555-0000",
                    "address_line_1": "123 Smart Ave",
                    "city": "Techville",
                    "postal_code": "00000",
                    "is_default": True
                }
            )

            # Create 5 "Delivered" orders
            for i in range(5):
                order = Order.objects.create(
                    user=customer,
                    shipping_address=address,
                    total_amount=0,
                    status='delivered',
                    paid=True
                )
                var = random.choice(variants)
                qty = random.randint(1, 3)
                OrderItem.objects.create(
                    order=order,
                    product_variant=var,
                    quantity=qty,
                    price=var.sale_price
                )
                order.total_amount = var.sale_price * qty
                order.save()
                
                random_past_days = random.randint(1, 10)
                Order.objects.filter(id=order.id).update(order_date=timezone.now() - timedelta(days=random_past_days))

            self.stdout.write(self.style.SUCCESS("Created 5 Delivered Orders."))

            # Create 2 "Processing" orders (for today)
            for i in range(2):
                order = Order.objects.create(
                    user=customer,
                    shipping_address=address,
                    total_amount=0,
                    status='processing',
                    paid=True
                )
                var = random.choice(variants)
                qty = random.randint(1, 3)
                OrderItem.objects.create(
                    order=order,
                    product_variant=var,
                    quantity=qty,
                    price=var.sale_price
                )
                order.total_amount = var.sale_price * qty
                order.save()

            self.stdout.write(self.style.SUCCESS("Created 2 Processing Orders."))

            # Create 2 "Shipped" orders (delayed by 4 days)
            for i in range(2):
                order = Order.objects.create(
                    user=customer,
                    shipping_address=address,
                    total_amount=0,
                    status='shipped',
                    paid=True
                )
                var = random.choice(variants)
                qty = random.randint(1, 3)
                OrderItem.objects.create(
                    order=order,
                    product_variant=var,
                    quantity=qty,
                    price=var.sale_price
                )
                order.total_amount = var.sale_price * qty
                order.save()
                
                Order.objects.filter(id=order.id).update(order_date=timezone.now() - timedelta(days=4))

            self.stdout.write(self.style.SUCCESS("Created 2 artificially delayed 'Shipped' Orders (for AI Anomaly Agent)."))
            
            self.stdout.write(self.style.SUCCESS("\nDatabase Seeded Successfully! The frontend catalog should now be populated."))
