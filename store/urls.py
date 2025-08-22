# store/urls.py
from django.urls import path
from . import views

# This defines the URL patterns for the 'store' app.
urlpatterns = [
    # When a user visits the root URL ('/'), call the HomePageView.
    path('', views.HomePageView.as_view(), name='home'),
    # When a user visits '/products/', call the ProductListView.
    path('products/', views.ProductListView.as_view(), name='product_list'),
]