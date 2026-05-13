from __future__ import annotations

from django.utils import timezone

from apps.finance.services import FxRateService
from store.models import ProductPriceHistory, ProductVariant


class PriceHistoryService:
    """Customer trust data for product price transparency."""

    @staticmethod
    def record_price_if_changed(sender, instance: ProductVariant, created: bool, **kwargs) -> None:
        last = instance.price_history.order_by("-changed_at").first()
        if created or not last or last.price != instance.sale_price or last.currency != instance.sale_currency:
            ProductPriceHistory.objects.create(
                product_variant=instance,
                price=instance.sale_price,
                currency=instance.sale_currency,
            )

    @staticmethod
    def chart_context(variant: ProductVariant) -> dict:
        since = timezone.now() - timezone.timedelta(days=30)
        history = list(variant.price_history.filter(changed_at__gte=since).values("changed_at", "price"))
        lowest = min([row["price"] for row in history] + [variant.sale_price])
        return {
            "price_history_data": [
                {"date": row["changed_at"].strftime("%b %d"), "price": float(row["price"])} for row in history
            ] or [{"date": timezone.now().strftime("%b %d"), "price": float(variant.sale_price)}],
            "lowest_30_day_price": lowest,
        }


class MarketplaceFxDisplayService:
    """Customer-facing currency equivalents for storefront pages."""

    @staticmethod
    def equivalents_for_try_price(price) -> dict:
        return {
            "USD": float(price / FxRateService.get_rate("USD", "TRY")),
            "EUR": float(price / FxRateService.get_rate("EUR", "TRY")),
        }


record_price_if_changed = PriceHistoryService.record_price_if_changed
