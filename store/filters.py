# multi_tenant_shop/store/filters.py
from django.db.models import Avg, F
import django_filters
from .models import Product, ProductVariant

class ProductFilter(django_filters.FilterSet):
    """
    A filter class to filter products based on different criteria.
    - price: Filters by product variant sale price range.
    - rating: Filters by the average rating of a product.
    - category: Filters by product category.
    """
    min_price = django_filters.NumberFilter(field_name='variants__sale_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='variants__sale_price', lookup_expr='lte')

    # This filter allows filtering by an average rating greater than or equal to the specified value.
    avg_rating = django_filters.NumberFilter(method='filter_by_rating', label='Minimum Rating')

    class Meta:
        model = Product
        fields = ['category']

    def filter_by_rating(self, queryset, name, value):
        """
        Custom method to filter products by their average rating.
        It annotates each product with its average rating and then filters
        based on the provided value.
        """
        # Annotate the queryset with the average rating of its reviews.
        # `Avg('reviews__rating')` calculates the average.
        # `rating_avg` is the name of the new field.
        return queryset.annotate(rating_avg=Avg('reviews__rating')).filter(rating_avg__gte=value)