# store/views.py
from django.views.generic import TemplateView, ListView, DetailView 
from .models import Product, ProductVariant, Order, OrderItem 

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .cart import Cart

from .forms import OrderCreateForm

from .forms import OrderCreateForm, CustomUserCreationForm
from django.contrib.auth import login

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

# This view will handle both displaying the checkout form (GET request)
# and processing the submitted form data (POST request).
def checkout(request):
    # Get the user's current cart from the session.
    cart = Cart(request)

    # Check if the form has been submitted using the POST method.
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request (binding).
        form = OrderCreateForm(request.POST)

        # Check if the form's data is valid according to our model's rules.
        if form.is_valid():
            # The form is valid. First, create the Address object in memory.
            # 'commit=False' prevents the form from saving to the DB immediately.
            # This allows us to modify the object before the final save.
            address = form.save(commit=False)

            # Check if the user is authenticated (logged in).
            if request.user.is_authenticated:
                # If logged in, associate this new address with the current user.
                address.user = request.user

            # Now, save the address to the database (either with or without a user).
            address.save()

            # Create a new Order record in the database.
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                shipping_address=address, # Link the order to the address we just saved.
                total_amount=cart.get_total_price() # Get the total from our cart object.
            )

            # Loop through every item currently in the cart.
            for item in cart:
                # For each item, create a corresponding OrderItem record in the database.
                OrderItem.objects.create(
                    order=order, # Link it to the order we just created.
                    product_variant=item['variant'],
                    price=item['price'], # Store the price at the time of purchase.
                    quantity=item['quantity']
                )

            # The order is successfully created, so clear the cart from the session.
            cart.clear()

            # Redirect the user to a success page (for now, we'll use the homepage).
            # Later, we can create a dedicated "Thank You" page.
            return redirect('store:home') 
    else:
        # If it's a GET request (the user is just visiting the page), create a blank form instance.
        form = OrderCreateForm()

    # Render the checkout template, passing the cart (for the summary) and the form.
    return render(request, 'store/checkout.html', {'cart': cart, 'form': form})

def signup(request):
    if request.method == 'POST':
        # If the form is submitted, create a form instance with the POST data.
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # If the form is valid, save the new user to the database.
            user = form.save()
            # Log the user in automatically after successful registration.
            login(request, user)
            # Redirect to the homepage.
            return redirect('store:home')
    else:
        # If it's a GET request, create a blank form.
        form = CustomUserCreationForm()

    return render(request, 'store/signup.html', {'form': form})