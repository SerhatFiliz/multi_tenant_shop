from django.urls import path, include
from django.contrib import admin

# This is the main URL configuration for every individual tenant (store).
# It will handle all requests coming to subdomains (e.g., inciboncuk.multitenantshop.com).

urlpatterns = [
    # 1. Store Management Admin Interface (Tenant specific)
    path('admin/', admin.site.urls), 

    # 2. All Customer-Facing Store Routes
    # This includes product listing, product detail, cart, checkout, customer login/signup/profile.
    # The 'store' namespace allows resolving URLs like 'store:cart_detail'
    path('', include('store.urls', namespace='store')),
    
    # Add other tenant-specific apps here if you have any (e.g., tenant_blog.urls)
]
