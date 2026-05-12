from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Order, Product, ProductVariant

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
    
    total_orders = Order.objects.count()
    recent_orders = Order.objects.select_related('user').order_by('-order_date')[:5]
    
    # Get pending orders for today
    from django.utils import timezone
    today = timezone.now().date()
    pending_orders = Order.objects.filter(status__in=['pending', 'processing']).order_by('-order_date')[:5]
    
    # Financial Analytics
    total_revenue = Order.objects.filter(paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Calculate total cost using OrderItem quantities and Variant cost_price
    # Ensure cost_price exists in ProductVariant model
    total_cost_data = Order.objects.filter(paid=True).aggregate(
        total_cost=Sum(F('items__quantity') * F('items__product_variant__cost_price'))
    )
    total_cost = total_cost_data['total_cost'] or 0
    
    profit_loss = total_revenue - total_cost

    from .models import StoreSettings
    store_settings, _ = StoreSettings.objects.get_or_create()

    context = {
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'profit_loss': profit_loss,
        'store_settings': store_settings,
    }
    return render(request, 'store/admin/nexus_dashboard.html', context)


@staff_member_required
def update_order_status(request, order_id):
    if request.method == "POST":
        order = Order.objects.get(id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            
            # Notification is now handled by Django Signals (store/signals.py)
            
    return redirect('store:nexus_dashboard')
