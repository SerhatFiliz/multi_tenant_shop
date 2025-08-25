# store_management/admin.py

from django.contrib import admin
from django.db.models import Sum, Count
# Import models from our 'store' app, as this app will read their data.
from store.models import Order, User 

# ==============================================================================
# CUSTOM ADMIN INDEX VIEW
# ==============================================================================
# We are overriding the default AdminSite's index method to pass
# custom context data to our custom admin/index.html template.

# First, we store a reference to the original index method, so we can call it later.
original_index = admin.site.index

def custom_index(request, *args, **kwargs):
    """
    This is our new, custom index view that will be used as the admin homepage.
    """
    # Use the Django ORM's aggregate function to calculate key metrics.
    
    # 1. Calculate Total Revenue
    # Sum('total_amount') calculates the sum of the 'total_amount' field for all Order records.
    total_revenue_data = Order.objects.aggregate(total_revenue=Sum('total_amount'))
    total_revenue = total_revenue_data['total_revenue'] or 0 # Use 0 if there are no orders yet.

    # 2. Calculate Total Orders
    # .count() is an efficient way to get the total number of records in a table.
    total_orders = Order.objects.count()
    
    # 3. Calculate Total Customers
    # We count all users that are active (is_staff=False filters out admins).
    total_users = User.objects.filter(is_active=True, is_staff=False).count()

    # Call the original index view that we saved earlier. This is important because
    # it does all the default work of getting the list of apps and models.
    response = original_index(request, *args, **kwargs)

    # Now, add our custom metrics to the context dictionary that will be
    # passed to the template.
    response.context_data['total_revenue'] = total_revenue
    response.context_data['total_orders'] = total_orders
    response.context_data['total_users'] = total_users

    return response

# Finally, we replace the default admin.site.index view with our custom one.
admin.site.index = custom_index