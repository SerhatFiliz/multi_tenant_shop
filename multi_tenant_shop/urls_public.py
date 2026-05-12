from django.urls import path, include
from django.contrib import admin
from django.views.generic import TemplateView # <-- TemplateView'i içe aktar
from django.conf import settings
from django.conf.urls.static import static

from store.views import MarketplaceHomeView

# The URL configuration used when the current schema is 'public' (Marketplace).
urlpatterns = [
    # 1. ROOT PATH: Use MarketplaceHomeView to explicitly render the marketplace home page.
    #    This ensures we load 'public_home.html' and fetches products across tenants.
    path('', MarketplaceHomeView.as_view(), name='public_home'),

    # 2. STORE URLs: Links like /search, /login, /signup, etc.
    path('', include('store.urls', namespace='store')),

    # 3. Store Management URLs: Manager Login/Register
    path("store-management/", include("store_management.urls", namespace="store_management")),
    
    # 4. Django Admin
    path("admin/", admin.site.urls),
]

# Debug and Media URLs
if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)