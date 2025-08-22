# store/urls.py
from django.urls import path
from . import views

# We are adding a new URL pattern for the product detail page.
urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    # This is a dynamic URL.
    # <slug:slug> tells Django: "Expect a URL-friendly string here,
    # capture it, and pass it to the view as a variable named 'slug'."
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]