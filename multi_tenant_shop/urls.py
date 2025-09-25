# multi_tenant_shop/multi_tenant_shop/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# JWT and API documentation imports
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# This section includes all the URL routing for the project.
urlpatterns = [
    # Main admin URL for the public schema.
    path('admin/', admin.site.urls),

    # ==========================================================================
    # API ENDPOINTS (Public & Shared)
    # ==========================================================================
    # These URLs are used by clients to obtain, refresh, and verify access tokens.
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Automatically generated API documentation endpoints.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Includes all URLs from the 'store' application.
    # This should include both API endpoints and regular web pages.
    path('', include('store.urls')),
    
    # Django Debug Toolbar URLs, active only in DEBUG mode.
    path('__debug__/', include('debug_toolbar.urls')),
]

# Serves media files (e.g., product images) in development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)