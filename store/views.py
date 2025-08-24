# store/views.py
from django.views.generic import TemplateView, ListView, DetailView # Add DetailView
from .models import Product, ProductVariant # Add Product

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .cart import Cart

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
    
@require_POST
def cart_add(request, variant_id):
    """
    A view to add a product variant to the cart.
    """
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    # For simplicity, we add quantity 1 for now. We will enhance this later.
    cart.add(variant=variant, quantity=1)
    return redirect('store:cart_detail') # Redirect to the cart detail page

def cart_detail(request):
    """
    A view to display the cart contents.
    """
    cart = Cart(request)
    return render(request, 'store/cart_detail.html', {'cart': cart})

def cart_remove(request, variant_id):
    """
    A view to remove an item from the cart.
    """
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    cart.remove(variant)
    return redirect('store:cart_detail')


@require_POST
def cart_update(request, variant_id):
    """
    A view to update the quantity of a specific item in the cart.
    """
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id)
    quantity = request.POST.get('quantity')

    if quantity and quantity.isdigit():
        cart.add(variant=variant, 
                 quantity=int(quantity), 
                 override_quantity=True) # override_quantity=True replaces the old quantity with the new one.
        
    return redirect('store:cart_detail')