from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

import requests
import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.utils import timezone

from store.models import ExchangeRateCache, Order, OrderItem, ProductVariant

logger = logging.getLogger(__name__)


class StripePaymentService:
    """Stripe checkout operations owned by the commerce Body."""

    @staticmethod
    def build_payment_intent(*, amount: Decimal, metadata: dict) -> stripe.PaymentIntent:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        return stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency="try",
            automatic_payment_methods={"enabled": True},
            metadata=metadata,
        )

    @staticmethod
    def mark_order_paid(payment_intent_id: str) -> Order | None:
        try:
            order = Order.objects.select_for_update().get(stripe_payment_intent_id=payment_intent_id)
        except Order.DoesNotExist:
            return None
        if not order.paid:
            order.paid = True
            order.status = "processing"
            order.save(update_fields=["paid", "status"])
        return order


class OrderCheckoutService:
    """Creates orders from a validated cart after Stripe confirmation."""

    @staticmethod
    def create_order_from_cart(*, user, address, cart, payment_intent_id: str) -> Order:
        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                shipping_address=address,
                total_amount=cart.get_total_price(),
                paid=False,
                status="pending",
                stripe_payment_intent_id=payment_intent_id,
            )
            for item in cart:
                variant = ProductVariant.objects.select_for_update().get(id=item["variant"].id)
                if variant.stock_quantity < item["quantity"]:
                    raise ValueError(f"Out of stock: not enough stock for {variant.product.name}.")
                variant.stock_quantity = F("stock_quantity") - item["quantity"]
                variant.save(update_fields=["stock_quantity"])
                OrderItem.objects.create(order=order, product_variant=variant, price=item["price"], quantity=item["quantity"])
        return order


class FxRateService:
    """Caches external FX rates for local profit calculations."""

    @staticmethod
    def get_rate(base: str, quote: str) -> Decimal:
        base = base.upper()
        quote = quote.upper()
        if base == quote:
            return Decimal("1")
        cached = ExchangeRateCache.objects.filter(
            base_currency=base,
            quote_currency=quote,
            fetched_at__gte=timezone.now() - timedelta(hours=6),
        ).first()
        if cached:
            return cached.rate

        api_key = getattr(settings, "EXCHANGE_RATE_API_KEY", "") or ""
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}" if api_key else f"https://open.er-api.com/v6/latest/{base}"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            rate = Decimal(str(response.json()["rates"][quote]))
        except Exception as exc:
            logger.warning("FX lookup failed for %s/%s: %s", base, quote, exc)
            fallback = {"USDTRY": "32.50", "EURTRY": "35.20", "USDEUR": "0.92", "EURUSD": "1.09"}
            rate = Decimal(fallback.get(f"{base}{quote}", "1"))

        ExchangeRateCache.objects.update_or_create(base_currency=base, quote_currency=quote, defaults={"rate": rate})
        return rate


class FinancialDashboardService:
    """Aggregates tenant-owned business intelligence for the dashboard."""

    @staticmethod
    def variant_profit_margin(variant: ProductVariant, local_currency: str = "TRY") -> Decimal:
        cost_rate = FxRateService.get_rate(variant.cost_currency, local_currency)
        sale_rate = FxRateService.get_rate(variant.sale_currency, local_currency)
        sale_local = variant.sale_price * sale_rate
        cost_local = variant.cost_price * cost_rate
        if sale_local == 0:
            return Decimal("0")
        return ((sale_local - cost_local) / sale_local * 100).quantize(Decimal("0.01"))

    @staticmethod
    def dashboard_series() -> dict:
        paid = Order.objects.filter(paid=True)
        total_cost = paid.aggregate(total=Sum(F("items__quantity") * F("items__product_variant__cost_price")))["total"] or Decimal("0")
        total_revenue = paid.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

        def rows(trunc):
            return list(
                paid.annotate(bucket=trunc("order_date"))
                .values("bucket")
                .annotate(revenue=Sum("total_amount"), orders=Count("id"))
                .order_by("bucket")
            )

        return {
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "profit": total_revenue - total_cost,
            "daily": rows(TruncDay),
            "weekly": rows(TruncWeek),
            "monthly": rows(TruncMonth),
        }


build_stripe_payment_intent = StripePaymentService.build_payment_intent
create_order_from_cart = OrderCheckoutService.create_order_from_cart
dashboard_series = FinancialDashboardService.dashboard_series
get_rate = FxRateService.get_rate
mark_order_paid = StripePaymentService.mark_order_paid
variant_profit_margin = FinancialDashboardService.variant_profit_margin
