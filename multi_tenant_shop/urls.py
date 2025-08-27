"""
URL configuration for multi_tenant_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# multi_tenant_shop/urls.py
from django.contrib import admin
from django.urls import path, include # Make sure to import 'include'
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # By adding the namespace parameter, we are telling the main URL router
    # that all URLs included from 'store.urls' belong to the 'store' namespace.
    # This allows us to use {% url 'store:cart_detail' %} in our templates.
    path('', include('store.urls', namespace='store')),
    
]


# --- DEVELOPMENT ONLY SETTINGS ---
# This block adds special URL patterns that are only needed during development.
# It will not run when DEBUG is False in a production environment.
if settings.DEBUG:
    # 1. Add URLs for Django Debug Toolbar
    # This must be imported only when DEBUG is True.
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    
    # 2. Add URLs for serving user-uploaded media files (like product images)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
