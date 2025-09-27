from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# Define the application namespace
app_name = "store_management"

# Ensure this list is correctly opened and closed with square brackets []
urlpatterns = [ 
    # --- Tenant (Store Owner) Registration ---
    # FIX: Set name="register" to match the URL reverse lookup used in public_home.html.
    path("register/", views.TenantCreateView.as_view(), name="register"),

    # --- Store Owner Authentication ---
    # Login page specifically for store management (public schema login).
    path("login/", auth_views.LoginView.as_view(template_name="store_management/login.html"), name="login"),
    
    # Logout view.
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # --- Dashboard (Store Management Landing Page) ---
    # The default route for store management after login.
    path("", views.DashboardView.as_view(), name="dashboard"),
] # Listeyi bu köşeli parantezle (]) kapattığınızdan emin olun