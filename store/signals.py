from django.db.models.signals import post_save
from django.dispatch import receiver
from store.models import Order
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Order)
def order_status_changed_notification(sender, instance, created, **kwargs):
    if not created:
        print(f"--- EMAIL SIMULATION (SIGNAL) ---")
        print(f"To: {instance.user.email if instance.user else 'Guest'}")
        print(f"Subject: Your Order #{instance.id} is now {instance.status.title()}!")
        print(f"Body: Dear Customer, your order status has been updated to {instance.status}.")
        print(f"---------------------------------")
        # Actual email code would be here
        # send_mail(
        #     subject=f"Your Order #{instance.id} is now {instance.status.title()}!",
        #     message=f"Dear Customer, your order status has been updated to {instance.status}.",
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[instance.user.email] if instance.user else [],
        #     fail_silently=True,
        # )