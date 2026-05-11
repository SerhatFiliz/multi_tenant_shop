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
    
    total_orders = Order.objects.count()
    recent_orders = Order.objects.select_related('user').order_by('-order_date')[:5]
    
    # Get pending orders for today
    from django.utils import timezone
    today = timezone.now().date()
    pending_orders = Order.objects.filter(status__in=['pending', 'processing']).order_by('-order_date')[:5]
    
    context = {
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
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
            
            # Trigger automated Email Simulation
            print(f"--- EMAIL SIMULATION ---")
            print(f"To: {order.user.email if order.user else 'Guest'}")
            print(f"Subject: Your Order #{order.id} is now {new_status.title()}!")
            print(f"Body: Dear Customer, your order status has been updated to {new_status}.")
            print(f"------------------------")
            
    return redirect('store:nexus_dashboard')
