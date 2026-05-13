import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from store.models import (
    Address,
    Category,
    Domain,
    Message,
    Order,
    OrderItem,
    Product,
    ProductPriceHistory,
    ProductVariant,
    Review,
    Tenant,
    Wishlist,
)

User = get_user_model()


STORE_CONFIGS = [
    {
        "schema": "nexus_tech",
        "subdomain": "nexus-tech",
        "name": "Nexus Tech",
        "owner_email": "owner@nexus-tech.com",
        "category": ("Smart Tech", "smart-tech"),
        "orders": 15,
        "message_prompts": [
            "Merhaba, siparişim ne zaman kargoya verilir?",
            "Kargo takip numarası paylaşabilir misiniz? Biraz acil.",
            "Teslimat gecikti, bugün bilgi alabilir miyim?",
        ],
        "products": [
            ("NexusBook Pro 14", "AI-ready ultrabook for mobile teams.", "38999.00", "28200.00", 18),
            ("EdgeCam 4K", "Secure 4K video kit for offices and retail.", "8999.00", "5100.00", 24),
            ("SignalMesh Router", "High-density Wi-Fi mesh router for stores.", "5499.00", "3100.00", 30),
            ("DeskHub Dock", "USB-C productivity dock with dual display support.", "3299.00", "1850.00", 42),
            ("PulsePad Tablet", "Lightweight tablet for POS and inventory teams.", "11999.00", "7200.00", 16),
        ],
    },
    {
        "schema": "glow_style",
        "subdomain": "glow-style",
        "name": "Glow Style",
        "owner_email": "owner@glow-style.com",
        "category": ("Modern Fashion", "modern-fashion"),
        "orders": 10,
        "message_prompts": [
            "Merhaba, bu ürünlerde beden kalıbı dar mı?",
            "M ve L beden arasında kaldım, ölçü tablosu var mı?",
        ],
        "products": [
            ("Luna Blazer", "Tailored blazer with a clean modern silhouette.", "2499.00", "1320.00", 22),
            ("Aero Knit Set", "Soft knit matching set for daily wear.", "1899.00", "980.00", 35),
            ("Nova Satin Shirt", "Fluid satin shirt with relaxed fit.", "1299.00", "610.00", 40),
            ("City Wide-Leg Pants", "High-waist trousers designed for all-day movement.", "1699.00", "790.00", 28),
            ("Glow Trench Coat", "Water-resistant trench with premium lining.", "3599.00", "1950.00", 14),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the multiverse production demo with stores, products, orders, messages, and reviews."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding production demo ecosystem..."))

        for config in STORE_CONFIGS:
            public_owner = self._public_owner(config)
            tenant, _ = Tenant.objects.update_or_create(
                schema_name=config["schema"],
                defaults={
                    "name": config["name"],
                    "subdomain": config["subdomain"],
                    "owner": public_owner,
                    "is_approved": True,
                },
            )
            Domain.objects.update_or_create(
                domain=f"{config['subdomain']}.localhost",
                defaults={"tenant": tenant, "is_primary": True},
            )

            self.stdout.write(self.style.WARNING(f"Seeding {config['name']} ({tenant.schema_name})..."))
            owner = self._tenant_owner(config)
            customer = self._customer()
            review_users = [customer] + [self._review_user(i) for i in range(1, 5)]
            address = self._address(customer, config["name"])

            tenant_products = Product.objects.filter(store=tenant) | Product.objects.filter(slug__startswith=f"{config['subdomain']}-")
            tenant_variants = ProductVariant.objects.filter(product__in=tenant_products)
            Message.objects.filter(store=tenant).delete()
            OrderItem.objects.filter(order__store=tenant).delete()
            OrderItem.objects.filter(product_variant__in=tenant_variants).delete()
            Order.objects.filter(store=tenant).delete()
            Review.objects.filter(product__store=tenant).delete()
            Wishlist.objects.filter(user=customer, products__store=tenant).delete()
            ProductPriceHistory.objects.filter(product_variant__product__store=tenant).delete()
            tenant_variants.delete()
            tenant_products.delete()

            category, _ = Category.objects.update_or_create(
                slug=config["category"][1],
                defaults={"name": config["category"][0]},
            )
            variants = self._products(config, tenant, category)
            self._orders(config["orders"], tenant, customer, address, variants)
            self._messages(config, customer, owner, tenant)
            self._reviews(review_users, variants)
            self._wishlist(customer, tenant, variants[:3])

        self.stdout.write(self.style.SUCCESS("Production demo ecosystem is ready."))

    def _public_owner(self, config):
        owner, _ = User.objects.get_or_create(
            username=config["owner_email"],
            defaults={"email": config["owner_email"], "is_staff": True, "tenant_role": User.ROLE_ADMIN},
        )
        owner.email = config["owner_email"]
        owner.is_staff = True
        owner.tenant_role = User.ROLE_ADMIN
        owner.set_password("admin123")
        owner.save()
        return owner

    def _tenant_owner(self, config):
        owner, _ = User.objects.get_or_create(
            username=config["owner_email"],
            defaults={"email": config["owner_email"], "is_staff": True, "tenant_role": User.ROLE_ADMIN},
        )
        owner.email = config["owner_email"]
        owner.is_staff = True
        owner.tenant_role = User.ROLE_ADMIN
        owner.set_password("admin123")
        owner.save()
        return owner

    def _customer(self):
        customer, _ = User.objects.get_or_create(
            username="customer@demo.com",
            defaults={"email": "customer@demo.com", "tenant_role": User.ROLE_CUSTOMER},
        )
        customer.email = "customer@demo.com"
        customer.tenant_role = User.ROLE_CUSTOMER
        customer.set_password("admin123")
        customer.save()
        return customer

    def _review_user(self, index):
        email = f"reviewer{index}@demo.com"
        user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
        user.email = email
        user.tenant_role = User.ROLE_CUSTOMER
        user.set_password("admin123")
        user.save()
        return user

    def _address(self, customer, store_name):
        return Address.objects.update_or_create(
            user=customer,
            address_title=f"{store_name} Demo Address",
            defaults={
                "full_name": "Demo Customer",
                "phone_number": "555-0101",
                "address_line_1": "Maslak Demo Plaza No: 42",
                "city": "Istanbul",
                "postal_code": "34398",
                "is_default": True,
            },
        )[0]

    def _products(self, config, tenant, category):
        variants = []
        for index, (name, description, price, cost, stock) in enumerate(config["products"], start=1):
            product = Product.objects.create(
                store=tenant,
                category=category,
                name=name,
                slug=f"{config['subdomain']}-{slugify(name)}",
                description=description,
                is_active=True,
            )
            
            # Use dynamic port lookup logic for image URLs (8001) as requested
            # We store the relative path, the template/settings will handle the base URL
            image_name = f"product_images/demo_{config['schema']}_{index}.jpg"
            
            v = ProductVariant.objects.create(
                product=product,
                sku=f"{config['subdomain'].upper()}-{index:03d}",
                color=random.choice(["Black", "White", "Blue", "Stone", "Graphite"]),
                size=random.choice(["S", "M", "L", "Standard", "14-inch"]),
                sale_price=Decimal(price),
                cost_price=Decimal(cost),
                stock_quantity=stock,
                is_active=True,
            )
            v.image.name = image_name
            v.save()
            variants.append(v)
            self._price_history(variants[-1])
        
        # Force-run Product.objects.rebuild() as requested for Treebeard/MPTT logic
        try:
            if hasattr(Product.objects, 'rebuild'):
                Product.objects.rebuild()
                self.stdout.write(self.style.SUCCESS("Product tree rebuilt successfully."))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Product.objects.rebuild() skipped: {e}"))

        # Direct check in the seeder code
        count = Product.objects.all().count()
        self.stdout.write(self.style.SUCCESS(f"Products in database: {count}"))
        
        return variants

    def _price_history(self, variant):
        base_price = variant.sale_price
        ProductPriceHistory.objects.filter(product_variant=variant).delete()
        for index in range(10):
            days_ago = 30 - (index * 3)
            drift = Decimal(random.choice(["-0.08", "-0.05", "-0.03", "0.00", "0.04", "0.07"]))
            price = (base_price * (Decimal("1.00") + drift)).quantize(Decimal("0.01"))
            point = ProductPriceHistory.objects.create(
                product_variant=variant,
                price=price,
                currency=variant.sale_currency,
            )
            ProductPriceHistory.objects.filter(id=point.id).update(changed_at=timezone.now() - timedelta(days=max(days_ago, 0)))

    def _orders(self, count, tenant, customer, address, variants):
        statuses = ["delivered", "delivered", "delivered", "shipped", "processing"]
        for index in range(count):
            variant = random.choice(variants)
            quantity = random.randint(1, 3)
            status = statuses[index % len(statuses)]
            order = Order.objects.create(
                store=tenant,
                user=customer,
                shipping_address=address,
                total_amount=variant.sale_price * quantity,
                status=status,
                paid=True,
            )
            OrderItem.objects.create(order=order, product_variant=variant, quantity=quantity, price=variant.sale_price)
            days_ago = int((index / max(count - 1, 1)) * 30)
            Order.objects.filter(id=order.id).update(order_date=timezone.now() - timedelta(days=days_ago))

    def _messages(self, config, customer, owner, tenant):
        for index, content in enumerate(config["message_prompts"]):
            high_priority = "acil" in content.lower() or "gecikti" in content.lower()
            message = Message.objects.create(
                sender=customer,
                receiver=owner,
                store=tenant,
                content=content,
                sentiment="Urgent" if high_priority else "Neutral",
                is_high_priority=high_priority,
            )
            Message.objects.filter(id=message.id).update(timestamp=timezone.now() - timedelta(hours=6 * index))

    def _reviews(self, users, variants):
        comments = [
            "Kalitesi beklentimin uzerinde, tekrar alirim.",
            "Paketleme ve teslimat cok iyiydi.",
            "Fiyat performans dengesi basarili.",
            "Urun anlatildigi gibi, destek ekibi hizli.",
            "Magaza deneyimi gayet profesyonel.",
        ]
        for index, variant in enumerate(variants):
            Review.objects.create(
                product=variant.product,
                user=users[index % len(users)],
                rating=5 if index % 2 == 0 else 4,
                comment=comments[index % len(comments)],
            )

    def _wishlist(self, customer, tenant, variants):
        wishlist, _ = Wishlist.objects.get_or_create(user=customer)
        existing_products = list(wishlist.products.exclude(store=tenant))
        wishlist.products.set(existing_products + [variant.product for variant in variants])
