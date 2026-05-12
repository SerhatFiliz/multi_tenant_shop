# store/tasks.py

import logging

import requests
from celery import shared_task
from django.core.mail import send_mail

from .models import Order

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Existing task — preserved exactly as before.
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# New task — notifies the SaaS AI Brain of a newly created order.
# ---------------------------------------------------------------------------

# Target URL of the SaaS AI Brain webhook endpoint.
_SAAS_BRAIN_URL = "http://localhost:8001/api/v1/webhooks/store-event"
# API key must match SAAS_API_KEY in the FastAPI service's environment.
_SAAS_API_KEY   = "demo-tenant-key-123"


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    name="store.tasks.notify_saas_ai_brain",
)
def notify_saas_ai_brain(self, order_data: dict, tenant_schema: str) -> str:
    """
    Sends an `order.created` event to the KOBİ SaaS AI Brain via HTTP POST.

    Args:
        order_data:     Serialisable dict describing the new order
                        (e.g. id, total_amount, items, user email).
        tenant_schema:  The django-tenants schema name of the originating store.
                        Used as `store_id` so the AI Brain can route by tenant.

    Returns:
        A human-readable result string for Celery's task result backend.

    Retries up to 3 times with a 10-second delay on network / server errors.
    """
    payload = {
        "event_type": "order.created",
        "store_id":   tenant_schema,
        "payload":    order_data,
    }
    try:
        response = requests.post(
            _SAAS_BRAIN_URL,
            json=payload,
            headers={"X-API-KEY": _SAAS_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        logger.info(
            "[SaaS Brain] Event dispatched — store=%s, order_id=%s, status=%s",
            tenant_schema,
            order_data.get("order_id"),
            response.status_code,
        )
        return f"Event dispatched to SaaS Brain: HTTP {response.status_code}"

    except requests.RequestException as exc:
        logger.warning(
            "[SaaS Brain] Dispatch failed — store=%s, error=%s. Retrying…",
            tenant_schema,
            exc,
        )
        # Celery will retry automatically up to max_retries times.
        raise self.retry(exc=exc)