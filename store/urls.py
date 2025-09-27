#store/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'store'

urlpatterns = [
    # --- Home & Product URLs ---
    path('', views.HomePageView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/<str:sku>/', views.ProductDetailView.as_view(), name='product_detail_variant'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # --- Cart & Checkout URLs ---
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:variant_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:variant_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    
    # --- User Authentication & Profile URLs ---
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/address/add/', views.add_address, name='add_address'),
    path('profile/address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('profile/address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    
    # --- Review & Wishlist URLs ---
    path('product/<slug:slug>/review/', views.submit_review, name='submit_review'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('add-to-wishlist/<slug:slug>/', views.add_to_wishlist, name='add_to_wishlist'),
    
    # --- Search URL ---
    path('search/', views.search, name='search'),

    # --- API Endpoints (For AJAX/JavaScript) ---
    path('api/cart/update/', views.cart_update_api, name='cart_update_api'),
    path('api/cart/remove/', views.cart_remove_api, name='cart_remove_api'),
]