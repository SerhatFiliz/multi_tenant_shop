from django.urls import path, include
from django.conf import settings

# Bu dosya, tenant şemalarda kullanılan URL'leri içerir.
urlpatterns = [
    path("", include("store.urls")),
]

# DEBUG Toolbar URL'lerini buraya da ekleyin ki kiracılar altında çalışabilsin.
if settings.DEBUG:
    try:
        # Debug Toolbar'ı dinamik olarak ekle
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    except ImportError:
        # Üretimde hata vermemesi için
        pass    