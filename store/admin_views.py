import json
import urllib.error
import urllib.request
from decimal import Decimal

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Order, Product, ProductVariant, Message
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import TenantInviteForm
from apps.finance.services import dashboard_series, variant_profit_margin
from apps.onboarding.services import invite_tenant_user


def role_required(*roles):
    def decorator(view_func):
        def wrapped(request, *args, **kwargs):
            if request.user.is_superuser or getattr(request.user, "tenant_role", None) in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission for that action.")
            return redirect("store:nexus_dashboard")
        return wrapped
    return decorator


def _local_campaign_suggestions(products):
    event_name = "Summer Sale"
    candidates = sorted(products, key=lambda item: (item.get("sold_units", 0), -item.get("stock", 0)))[:4]
    suggestions = []
    for product in candidates:
        discount = 18 if product.get("stock", 0) >= 25 and product.get("sold_units", 0) <= 1 else 12
        old_price = Decimal(str(product.get("price", 0)))
        new_price = (old_price * (Decimal("100") - Decimal(discount)) / Decimal("100")).quantize(Decimal("0.01"))
        suggestions.append(
            {
                "variant_id": product["variant_id"],
                "product_name": product["name"],
                "reason": f"Stock is {product.get('stock', 0)} while recent sold units are {product.get('sold_units', 0)}; timed for {event_name}.",
                "event": event_name,
                "discount_percent": discount,
                "old_price": old_price,
                "new_price": new_price,
                "expected_impact": "Designed to convert slow-moving stock without over-discounting the catalog.",
            }
        )
    return suggestions


@staff_member_required
def nexus_dashboard(request):
    """
    Nexus-Admin Dashboard for the Tenant Store Owner.
    Premium, dark-themed dashboard.
    """
    # Just passing context to render the template. The template will use JS to fetch
    # analytics from the FastAPI backend.
    
    # Calculate Analytics in Django
    from django.db.models import Sum, F
    
    order_qs = Order.objects.filter(store=request.tenant)
    variant_qs = ProductVariant.objects.filter(product__store=request.tenant)
    total_orders = order_qs.count()
    recent_orders = order_qs.select_related('user').order_by('-order_date')[:5]
    
    # Get pending orders for today
    from django.utils import timezone
    today = timezone.now().date()
    pending_orders = order_qs.filter(status__in=['pending', 'processing']).order_by('-order_date')[:5]
    
    # Financial Analytics
    total_revenue = order_qs.filter(paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Calculate total cost using OrderItem quantities and Variant cost_price
    # Ensure cost_price exists in ProductVariant model
    total_cost_data = order_qs.filter(paid=True).aggregate(
        total_cost=Sum(F('items__quantity') * F('items__product_variant__cost_price'))
    )
    total_cost = total_cost_data['total_cost'] or 0
    
    profit_loss = total_revenue - total_cost

    from .models import StoreSettings
    store_settings, _ = StoreSettings.objects.get_or_create()
    series = dashboard_series()
    invite_form = TenantInviteForm()
    variants = variant_qs.select_related("product")[:12]
    store_messages = Message.objects.filter(store=request.tenant, sender__is_staff=False).select_related("sender", "receiver").order_by("-is_high_priority", "-timestamp")[:12]
    unread_message_count = Message.objects.filter(store=request.tenant, receiver=request.user, is_read=False).count()
    business_context = _business_context(request)

    products = Product.objects.filter(store=request.tenant).select_related('category').prefetch_related('variants')[:10]

    context = {
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'profit_loss': profit_loss,
        'store_settings': store_settings,
        'business_series': series,
        'invite_form': invite_form,
        'variants': variants,
        'products': products,
        'store_messages': store_messages,
        'unread_message_count': unread_message_count,
        'last_message_id': store_messages[0].id if store_messages else 0,
        'ai_service_base_url': settings.AI_SERVICE_BASE_URL,
        'store_slug': getattr(request.tenant, "subdomain", None) or request.tenant.schema_name,
        'campaign_suggestions': _local_campaign_suggestions(business_context["products"]),
    }
    return render(request, 'store/admin/nexus_dashboard.html', context)


@staff_member_required
@role_required("admin", "editor", "support")
def manager_products(request):
    variants = ProductVariant.objects.filter(product__store=request.tenant).select_related("product", "product__category").order_by("product__name")
    return render(request, "store/admin/manager_products.html", {"variants": variants})


def _business_context(request):
    from django.db.models import Count, Sum
    variants = ProductVariant.objects.filter(product__store=request.tenant).select_related("product", "product__category").order_by("product__name")
    sales = {
        row["items__product_variant"]: row["qty"] or 0
        for row in Order.objects.filter(store=request.tenant, paid=True).values("items__product_variant").annotate(qty=Sum("items__quantity"))
    }
    products = []
    for variant in variants:
        sold = int(sales.get(variant.id, 0))
        products.append(
            {
                "product_id": variant.product.id,
                "variant_id": variant.id,
                "name": variant.product.name,
                "category": variant.product.category.name,
                "sku": variant.sku,
                "price": float(variant.sale_price),
                "cost": float(variant.cost_price),
                "stock": variant.stock_quantity,
                "sold_units": sold,
                "margin": float(variant_profit_margin(variant)),
            }
        )
    order_qs = Order.objects.filter(store=request.tenant)
    revenue = order_qs.filter(paid=True).aggregate(total=Sum("total_amount"))["total"] or 0
    return {
        "store_slug": getattr(request.tenant, "subdomain", None) or request.tenant.schema_name,
        "store_name": request.tenant.name,
        "orders": {
            "total": order_qs.count(),
            "pending": order_qs.filter(status__in=["pending", "processing"]).count(),
            "paid": order_qs.filter(paid=True).count(),
            "revenue": float(revenue),
        },
        "products": products,
    }


@staff_member_required
def manager_context_json(request):
    return JsonResponse(_business_context(request))


@staff_member_required
def manager_messages_poll(request):
    after_id = int(request.GET.get("after_id") or 0)
    qs = Message.objects.filter(store=request.tenant, sender__is_staff=False, id__gt=after_id).select_related("sender", "receiver").order_by("id")
    return JsonResponse(
        {
            "messages": [
                {
                    "id": message.id,
                    "content": message.content,
                    "sender": message.sender.email or message.sender.username,
                    "timestamp": message.timestamp.strftime("%H:%M"),
                    "is_high_priority": message.is_high_priority,
                    "sentiment": message.sentiment,
                    "customer_id": message.sender_id,
                }
                for message in qs[:50]
            ]
        }
    )


@staff_member_required
@role_required("admin", "support")
@require_POST
def reply_message_json(request):
    customer_id = request.POST.get("customer_id")
    content = (request.POST.get("content") or "").strip()
    if not customer_id or not content:
        return JsonResponse({"error": "customer_id and content are required."}, status=400)
    from .models import User
    customer = User.objects.get(id=customer_id)
    message = Message.objects.create(sender=request.user, receiver=customer, store=request.tenant, content=content, sentiment="Merchant Reply")
    return JsonResponse({"message": {"id": message.id, "content": message.content, "sender": request.user.email or request.user.username, "timestamp": message.timestamp.strftime("%H:%M")}})


@staff_member_required
@role_required("admin", "editor")
@require_POST
def apply_campaign(request):
    variant_id = request.POST.get("variant_id")
    discount_percent = Decimal(str(request.POST.get("discount_percent") or "0"))
    try:
        variant = ProductVariant.objects.select_related("product").get(id=variant_id, product__store=request.tenant)
    except ProductVariant.DoesNotExist:
        return JsonResponse({"error": "Product variant not found."}, status=404)
    if discount_percent <= 0 or discount_percent >= 90:
        return JsonResponse({"error": "Invalid discount percent."}, status=400)
    old_price = variant.sale_price
    new_price = (old_price * (Decimal("100") - discount_percent) / Decimal("100")).quantize(Decimal("0.01"))
    variant.sale_price = new_price
    variant.save(update_fields=["sale_price"])
    if request.POST.get("redirect") == "1":
        messages.success(request, f"Kampanya uygulandi: {variant.product.name} %{discount_percent}")
        return redirect("store:nexus_dashboard")
    return JsonResponse(
        {
            "status": "applied",
            "product": variant.product.name,
            "old_price": float(old_price),
            "new_price": float(new_price),
            "discount_percent": float(discount_percent),
        }
    )


@staff_member_required
@role_required("admin", "support")
def update_order_status(request, order_id):
    if request.method == "POST":
        order = Order.objects.get(id=order_id, store=request.tenant)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            
            # Notification is handled by the store.signals package.
            
    return redirect('store:nexus_dashboard')

@staff_member_required
@role_required("admin", "editor")
def add_product(request):
    """
    Handles form submission from Nexus Dashboard to add a new product and variant.
    """
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        price = request.POST.get("price")
        cost_price = request.POST.get("cost_price") or 0
        cost_currency = request.POST.get("cost_currency") or "TRY"
        stock = request.POST.get("stock")
        category_id = request.POST.get("category")
        
        from .models import Category
        category = Category.objects.filter(id=category_id).first()
        if not category:
            # Fallback to a default category or create one
            category, _ = Category.objects.get_or_create(name="General", slug="general")
            
        from django.utils.text import slugify
        import uuid
        base_slug = slugify(name)
        unique_slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        
        product = Product.objects.create(
            store=request.tenant,
            name=name,
            slug=unique_slug,
            description=description,
            category=category,
            is_active=True
        )
        
        ProductVariant.objects.create(
            product=product,
            sku=f"SKU-{uuid.uuid4().hex[:8].upper()}",
            sale_price=price,
            sale_currency="TRY",
            cost_price=cost_price,
            cost_currency=cost_currency,
            stock_quantity=stock,
            is_active=True
        )
        
    return redirect('store:nexus_dashboard')

@staff_member_required
def toggle_live_chat(request):
    if request.method == "POST":
        from .models import StoreSettings
        store_settings, _ = StoreSettings.objects.get_or_create()
        store_settings.live_chat_override = not store_settings.live_chat_override
        store_settings.save()
    return redirect('store:nexus_dashboard')


@staff_member_required
@role_required("admin")
@require_POST
def invite_user(request):
    form = TenantInviteForm(request.POST)
    if form.is_valid():
        invite_tenant_user(
            email=form.cleaned_data["email"],
            role=form.cleaned_data["role"],
            invited_by=request.user,
        )
        messages.success(request, "Invitation sent.")
    else:
        messages.error(request, "Invitation could not be sent.")
    return redirect("store:nexus_dashboard")


@staff_member_required
def finance_json(request):
    series = dashboard_series()
    return JsonResponse(
        {
            "daily": [{"label": r["bucket"].strftime("%b %d"), "revenue": float(r["revenue"] or 0), "orders": r["orders"]} for r in series["daily"]],
            "weekly": [{"label": r["bucket"].strftime("%b %d"), "revenue": float(r["revenue"] or 0), "orders": r["orders"]} for r in series["weekly"]],
            "monthly": [{"label": r["bucket"].strftime("%b %Y"), "revenue": float(r["revenue"] or 0), "orders": r["orders"]} for r in series["monthly"]],
            "profit": float(series["profit"]),
        }
    )


@staff_member_required
def profit_margin_json(request, variant_id):
    variant = ProductVariant.objects.get(id=variant_id)
    return JsonResponse({"sku": variant.sku, "margin": float(variant_profit_margin(variant))})


@staff_member_required
@role_required("admin", "support")
@require_POST
def reply_message(request, message_id):
    original = Message.objects.select_related("sender", "store").get(id=message_id, store=request.tenant)
    content = (request.POST.get("content") or "").strip()
    if not content:
        messages.error(request, "Reply cannot be empty.")
        return redirect("store:nexus_dashboard")

    Message.objects.create(
        sender=request.user,
        receiver=original.sender,
        store=original.store,
        content=content,
        sentiment="Merchant Reply",
    )
    original.is_read = True
    original.save(update_fields=["is_read"])
    messages.success(request, "Reply sent to customer.")
    return redirect("store:nexus_dashboard")
