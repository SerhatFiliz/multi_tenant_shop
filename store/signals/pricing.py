from __future__ import annotations

from django.db.models.signals import post_save

from apps.marketplace.services import PriceHistoryService
from store.models import ProductVariant

post_save.connect(
    PriceHistoryService.record_price_if_changed,
    sender=ProductVariant,
    dispatch_uid="store.product_variant.price_history",
)
