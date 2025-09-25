from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'store'

# The main URL patterns for the web pages.
urlpatterns = [
    # Home and product listing pages
    path('', views.HomePageView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    
    # Product detail URLs.
    # The more specific URL pattern with an SKU must come first so Django can match it.
    path('product/<slug:slug>/<str:sku>/', views.ProductDetailView.as_view(), name='product_detail_variant'),
    
    # The generic product detail URL. This is a fallback if no SKU is provided.
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Cart URLs
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:variant_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:variant_id>/', views.cart_remove, name='cart_remove'),
    
    # API URLs for AJAX-based cart updates (Added this section)
    path('api/cart/update/', views.cart_update, name='cart_update_api'),
    path('api/cart/remove/', views.cart_remove_api, name='cart_remove_api'),

    # Checkout URL
    path('checkout/', views.checkout, name='checkout'),

    # User authentication URLs
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # User profile and address management
    path('profile/', views.profile, name='profile'),
    path('profile/address/add/', views.add_address, name='add_address'),
    path('profile/address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('profile/address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    
    # Product review URLs
    path('product/<slug:slug>/review/', views.submit_review, name='submit_review'),

    # Search URL
    path('search/', views.search, name='search'),

    # Wishlist URLs
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('add-to-wishlist/<slug:slug>/', views.add_to_wishlist, name='add_to_wishlist'),
]