# store/views.py
from django.views.generic import TemplateView, ListView
from .models import ProductVariant

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