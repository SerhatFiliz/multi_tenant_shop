from django.urls import path, include
from django.contrib import admin
from store import admin_views

# This is the main URL configuration for every individual tenant (store).
# It will handle all requests coming to subdomains (e.g., inciboncuk.multitenantshop.com).

urlpatterns = [
    # 1. Store Management Admin Interface (Tenant specific)
    path('admin/dashboard/', admin_views.nexus_dashboard, name='nexus_dashboard'),
    path('admin/order/<int:order_id>/status/', admin_views.update_order_status, name='update_order_status'),
    path('admin/', admin.site.urls), 

    # 2. All Customer-Facing Store Routes
    # This includes product listing, product detail, cart, checkout, customer login/signup/profile.
    # The 'store' namespace allows resolving URLs like 'store:cart_detail'
    path('', include('store.urls', namespace='store')),
    
    # Add other tenant-specific apps here if you have any (e.g., tenant_blog.urls)
]
