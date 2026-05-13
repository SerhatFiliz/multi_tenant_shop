#store/urls.py
from django.urls import path
from . import views, admin_views
from django.contrib.auth import views as auth_views
from apps.finance.webhooks.stripe import stripe_webhook
from apps.onboarding.views import PublicRegisterView

app_name = 'store'

urlpatterns = [
    # --- Home & Product URLs ---
    path('', views.HomePageView.as_view(), name='home'),
    path('register/', PublicRegisterView.as_view(), name='public_register'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/<str:sku>/', views.ProductDetailView.as_view(), name='product_detail_variant'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('store/<slug:store_slug>/', views.StoreProfileView.as_view(), name='store_profile'),
    
    # --- Cart & Checkout URLs ---
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:variant_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:variant_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
    
    # --- User Authentication & Profile URLs ---
    path('signup/', views.signup, name='signup'),
    path('login/', views.UniversalLoginView.as_view(), name='login'),
    path('login/magic-link/', views.magic_link_request, name='magic_link'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('account/dashboard/', views.profile, name='account_dashboard'),
    path('messages/send/', views.send_store_message, name='send_store_message'),
    path('messages/live/send/', views.live_support_send, name='live_support_send'),
    path('messages/live/poll/', views.live_support_poll, name='live_support_poll'),
    path('profile/address/add/', views.add_address, name='add_address'),
    path('profile/address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('profile/address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    
    # --- Review & Wishlist URLs ---
    path('product/<slug:slug>/review/', views.submit_review, name='submit_review'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('add-to-wishlist/<slug:slug>/', views.add_to_wishlist, name='add_to_wishlist'),
    
    # --- Search URL ---
    path('search/', views.search, name='search'),

    # --- Nexus-Admin Dashboard ---
    path('nexus/dashboard/', admin_views.nexus_dashboard, name='nexus_dashboard'),
    path('nexus/products/', admin_views.manager_products, name='manager_products'),
    path('nexus/update-order/<int:order_id>/', admin_views.update_order_status, name='update_order_status'),
    path('nexus/add-product/', admin_views.add_product, name='add_product'),
    path('nexus/toggle-live-chat/', admin_views.toggle_live_chat, name='toggle_live_chat'),
    path('nexus/invite-user/', admin_views.invite_user, name='invite_user'),
    path('nexus/finance.json', admin_views.finance_json, name='finance_json'),
    path('nexus/context.json', admin_views.manager_context_json, name='manager_context_json'),
    path('nexus/messages/poll/', admin_views.manager_messages_poll, name='manager_messages_poll'),
    path('nexus/messages/reply.json', admin_views.reply_message_json, name='reply_message_json'),
    path('nexus/campaigns/apply/', admin_views.apply_campaign, name='apply_campaign'),
    path('nexus/profit-margin/<int:variant_id>.json', admin_views.profit_margin_json, name='profit_margin_json'),
    path('nexus/messages/<int:message_id>/reply/', admin_views.reply_message, name='reply_message'),

    # --- API Endpoints (For AJAX/JavaScript) ---
    path('api/cart/update/', views.cart_update_api, name='cart_update_api'),
    path('api/cart/remove/', views.cart_remove_api, name='cart_remove_api'),
    path('api/customer/catalog-context/', views.customer_catalog_context, name='customer_catalog_context'),
]

from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'api/products', views.ProductViewSet, basename='product')
urlpatterns += router.urls
