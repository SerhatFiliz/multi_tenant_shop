# store/urls.py
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Cart URLs
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:variant_id>/', views.cart_add, name='cart_add'),
    
    # --- ADD THESE TWO NEW URLS ---
    path('cart/remove/<int:variant_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:variant_id>/', views.cart_update, name='cart_update'),

    path('checkout/', views.checkout, name='checkout'),
]