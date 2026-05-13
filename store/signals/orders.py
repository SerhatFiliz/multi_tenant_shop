from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from store.models import Order


@receiver(post_save, sender=Order)
def order_status_changed_notification(sender, instance, created, **kwargs):
    if created:
        return
    customer_name = instance.user.first_name if instance.user and instance.user.first_name else "there"
    items = ", ".join(
        f"{item.quantity}x {item.product_variant.product.name}" for item in instance.items.select_related("product_variant__product")
    )
    print("--- EMAIL SIMULATION (SIGNAL) ---")
    print(f"To: {instance.user.email if instance.user else 'Guest'}")
    print(f"Subject: Your Order #{instance.id} is now {instance.status.title()}!")
    print(f"Body: Hi {customer_name}, your order #{instance.id} ({items or 'your items'}) is now {instance.status}.")
    print("---------------------------------")

