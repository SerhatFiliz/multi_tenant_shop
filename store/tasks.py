# store/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from .models import Order

@shared_task
def send_order_confirmation_email(order_id):
    """
    Asynchronous task to send an email notification when an order is successfully created.
    """
    try:
        order = Order.objects.get(id=order_id)
        subject = f'Siparişiniz Alındı - Sipariş #{order.id}'
        message = (
            f'Merhaba {order.user.first_name},\n\n'
            f'İnci Boncuk Tuhafiye\'den verdiğiniz #{order.id} numaralı siparişiniz başarıyla oluşturulmuştur.\n'
            f'Toplam Tutar: {order.total_amount} TL\n\n'
            f'Teşekkür ederiz!'
        )
        # We print the email to the console because of our EMAIL_BACKEND setting.
        send_mail(
            subject,
            message,
            'siparis@inciboncuk.com',
            [order.user.email]
        )
        return f"Confirmation email for order {order_id} sent successfully."
    except Order.DoesNotExist:
        return f"Order with id {order_id} does not exist."