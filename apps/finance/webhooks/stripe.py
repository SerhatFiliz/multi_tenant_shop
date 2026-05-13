from __future__ import annotations

import json

import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.finance.services import StripePaymentService


class StripePaymentWebhook:
    """Handles Stripe event verification and order payment state changes."""

    @staticmethod
    def parse_event(request):
        endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
        if endpoint_secret:
            return stripe.Webhook.construct_event(
                request.body,
                request.META.get("HTTP_STRIPE_SIGNATURE", ""),
                endpoint_secret,
            )
        return json.loads(request.body)

    @staticmethod
    def handle(event) -> None:
        if event.get("type") == "payment_intent.succeeded":
            intent = event["data"]["object"]
            with transaction.atomic():
                StripePaymentService.mark_order_paid(intent["id"])


@csrf_exempt
@require_POST
def stripe_webhook(request):
    try:
        event = StripePaymentWebhook.parse_event(request)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)
    StripePaymentWebhook.handle(event)
    return HttpResponse(status=200)

