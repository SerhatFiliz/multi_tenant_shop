    # store/views.py
from django.views.generic import TemplateView, ListView, DetailView 
from .models import Product, ProductVariant, Order, OrderItem, Review, Address, Category

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .cart import Cart

from .forms import OrderCreateForm

from .forms import OrderCreateForm, CustomUserCreationForm, ReviewForm
from django.contrib.auth import login

from django.contrib.auth.decorators import login_required

from .documents import ProductVariantDocument

# --- Dosyanın en üstündeki import satırlarına bunları ekle ---
from rest_framework import viewsets
from .serializers import ProductSerializer, CategorySerializer

import stripe
from django.conf import settings

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

        variants_data_for_js = list(variants_queryset.values(
            'id', 'sku', 'sale_price', 'stock_quantity', 'color', 'size'
        ))
        context['variants_data_for_js'] = variants_data_for_js

        # --- ADD THIS NEW LOGIC ---
        # Get all reviews for the current product.
        context['reviews'] = product.reviews.all().order_by('-created_at')
        # Create an instance of the review form to display on the page.
        context['review_form'] = ReviewForm()

        # Check if the current user (if logged in) has purchased this product.
        has_purchased = False
        if self.request.user.is_authenticated:
            has_purchased = Order.objects.filter(
                user=self.request.user,
                status__in=['delivered', 'shipped'],
                items__product_variant__product=product
            ).exists()
        context['has_purchased'] = has_purchased
        # --- END OF NEW LOGIC ---

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

# We make the checkout page login-required to simplify the process.
# We make the checkout page login-required to simplify the payment flow.
@login_required
def checkout(request):
    cart = Cart(request)
    # Set your secret key for the Stripe API.
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # This block is now triggered AFTER a successful payment on the frontend.
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()

            order = Order.objects.create(
                user=request.user,
                shipping_address=address,
                total_amount=cart.get_total_price()
            )

            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product_variant=item['variant'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            
            cart.clear()
            # We can add an order confirmation email here later using Celery.
            return redirect('store:profile') # Redirect to profile to see the new order.
    else:
        # This block runs when the page is first loaded (GET request).
        form = OrderCreateForm()
        intent = None
        # We only create a payment intent if the cart is not empty.
        if cart.get_total_price() > 0:
            try:
                # Create a PaymentIntent on Stripe's servers.
                # The amount is in the smallest currency unit (e.g., cents for USD, kuruş for TRY).
                intent = stripe.PaymentIntent.create(
                    amount=int(cart.get_total_price() * 100), # Amount in kuruş for TRY
                    currency='try', # Change if you use a different currency
                    automatic_payment_methods={'enabled': True},
                )
            except stripe.error.StripeError as e:
                # Handle potential errors from Stripe, e.g., if the amount is zero.
                print(f"Stripe Error: {e}")
        
    context = {
        'cart': cart,
        'form': form,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        # The client_secret is a temporary key for this specific payment.
        # It authorizes the frontend to confirm the payment.
        'client_secret': intent.client_secret if intent else None,
    }
    return render(request, 'store/checkout.html', context)

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

# The @login_required decorator is a security feature from Django.
# It ensures that only logged-in users can access this view.
# If an anonymous user tries to access it, they will be redirected to the login page.
@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    addresses = Address.objects.filter(user=request.user)

    # --- UPDATE THE CONTEXT ---
    context = {
        'orders': orders,
        'addresses': addresses
    }
    return render(request, 'store/profile.html', context)

@login_required # Only logged-in users can submit reviews.
def submit_review(request, slug):
    # Find the product that the user is trying to review.
    product = get_object_or_404(Product, slug=slug)
    
    # --- CRITICAL LOGIC: Check if the user has purchased this product ---
    # We check if there is any completed order ('delivered' or 'shipped')
    # for the current user that contains this specific product.
    has_purchased = Order.objects.filter(
        user=request.user,
        status__in=['delivered', 'shipped'], # Check against multiple statuses
        items__product_variant__product=product
    ).exists()

    if not has_purchased:
        # If the user has not purchased the item, redirect them back.
        # We should add a Django message here later to inform the user.
        return redirect('store:product_detail', slug=slug)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Create the review object in memory.
            review = form.save(commit=False)
            # Assign the current product and user to the review.
            review.product = product
            review.user = request.user
            # Save the complete review object to the database.
            review.save()
            # Redirect back to the product detail page to see the new review.
            return redirect('store:product_detail', slug=slug)
    else:
        form = ReviewForm()

    # Pass the purchase status to the template to conditionally show the form.
    return render(request, 'store/product_detail.html', {'form': form, 'product': product, 'has_purchased': has_purchased})


@login_required
def add_address(request):
    """
    Handles the creation of a new address for the logged-in user.
    """
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user # Associate the address with the current user
            address.save()
            return redirect('store:profile') # Redirect back to the profile page
    else:
        form = OrderCreateForm()
    return render(request, 'store/address_form.html', {'form': form})

@login_required
def edit_address(request, address_id):
    """
    Handles editing an existing address.
    """
    # get_object_or_404 ensures we only get the address if it exists AND belongs to the current user.
    # This is a crucial security measure.
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        # 'instance=address' pre-populates the form with the existing address data.
        form = OrderCreateForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('store:profile')
    else:
        form = OrderCreateForm(instance=address)
    return render(request, 'store/address_form.html', {'form': form, 'address': address})

@login_required
def delete_address(request, address_id):
    """
    Handles deleting an existing address.
    """
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        return redirect('store:profile')
    # If it's a GET request, we can optionally show a confirmation page.
    # For simplicity, we'll only handle POST for deletion.
    return redirect('store:profile')


def search(request):
    """
    Handles the search functionality by querying the Elasticsearch index.
    """
    # Get the search query from the URL's GET parameter named 'q'.
    query = request.GET.get('q', '')

    results = []
    if query:
        # If a query was submitted, perform the search.
        search_request = ProductVariantDocument.search()

        # Use a 'multi_match' query to search across multiple fields.
        # 'fuzziness="AUTO"' handles minor typos automatically.
        search_request = search_request.query(
            "multi_match",
            query=query,
            fields=['product_name', 'color', 'sku'],
            fuzziness="AUTO"
        )

        # Execute the search and get the response from Elasticsearch.
        results = search_request.execute()

    context = {
        'query': query,
        'results': results
    }
    return render(request, 'store/search_results.html', context)


# --- ProductViewSet sınıfını güncelle ---
class ProductViewSet(viewsets.ModelViewSet): # ReadOnlyModelViewSet'i ModelViewSet ile değiştir
    """
    This ViewSet now provides full 'list', 'create', 'retrieve',
    'update', and 'destroy' actions for Products.
    """
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    lookup_field = 'slug'

# --- CategoryViewSet sınıfını güncelle ---
class CategoryViewSet(viewsets.ModelViewSet): # ReadOnlyModelViewSet'i ModelViewSet ile değiştir
    """
    This ViewSet now provides full CRUD actions for Categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'