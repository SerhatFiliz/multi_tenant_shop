# store/views.py
from django.views.generic import TemplateView, ListView, DetailView # Add DetailView
from .models import Product, ProductVariant # Add Product

# We use Class-Based Views (CBVs) as they are a professional and reusable way
# to structure view logic.

class HomePageView(TemplateView):
    """
    A simple view that just renders a static template for the homepage.
    """
    template_name = "home.html"

class ProductListView(ListView):
    """
    This view fetches a list of objects from the database and passes them
    to a template. It's perfect for a product listing page.
    """
    model = ProductVariant  # Which model should I get data from?
    template_name = 'store/product_list.html'  # Which template should I send the data to?
    context_object_name = 'variants'  # What should the list of objects be called in the template?

    def get_queryset(self):
        """
        We override this method to control which objects are listed.
        Here, we only want to show variants that are active and have stock.
        """
        return ProductVariant.objects.filter(is_active=True, stock_quantity__gt=0)
    
class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        variants_queryset = product.variants.filter(is_active=True)
        context['variants'] = variants_queryset
        
        # This part is crucial. It prepares a simple list for JavaScript.
        variants_data_for_js = list(variants_queryset.values(
            'id', 
            'sku', 
            'sale_price', 
            'stock_quantity', 
            'color', 
            'size'
        ))
        context['variants_data_for_js'] = variants_data_for_js
        
        return context