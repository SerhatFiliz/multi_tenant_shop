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

from .tasks import send_order_confirmation_email

from django.http import JsonResponse
import json

# We use Class-Based Views (CBVs) as they are a professional and reusable way
# to structure view logic.

class HomePageView(TemplateView):
    """
    A simple view that just renders a static template for the homepage.
    """
    template_name = "home.html"

class ProductListView(ListView):
    """
    This view now has a single, simple job: to display a list of
    all active product variants from the database.
    All smart searching is now handled by our 'search' view and Elasticsearch.
    """
    model = ProductVariant
    template_name = 'store/product_list.html'
    context_object_name = 'variants'
    paginate_by = 12 

    def get_queryset(self):
        """
        We override this to fetch all active variants and optimize the database query.
        """
        # We use select_related to prevent extra database queries in the template.
        return ProductVariant.objects.filter(is_active=True).select_related('product__category')

    
class ProductDetailView(DetailView):
    """
    Handles the logic for displaying a single product page.
    It fetches the main product object based on the URL slug and then gathers
    all related data, such as variants and reviews, to pass to the template.
    """
    model = Product # Let DetailView handle finding the correct Product
    template_name = 'store/product_detail.html'
    # By default, DetailView uses 'slug' from the URL to lookup the object in the 'Product' model.
    
    def get_context_data(self, **kwargs):
        """
        Overrides the default method to inject additional context data into the template.
        """
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # --- Variant Data ---
        # Fetch all active variants related to this product.
        variants_queryset = product.variants.filter(is_active=True)
        context['variants'] = variants_queryset

        # --- Data for JavaScript ---
        variants_data_for_js = list(variants_queryset.values(
            'id', 'sku', 'sale_price', 'stock_quantity', 'color', 'size', 'image'
        ))
        context['variants_data_for_js'] = variants_data_for_js

        # --- Logic to Determine the Initial Variant to Display ---
        selected_variant_id = self.request.GET.get('variant_id')
        initial_variant = variants_queryset.first() # Default to the first variant.

        if selected_variant_id:
            try:
                # Try to find the variant that was clicked from the list page.
                selected_variant_as_object = variants_queryset.get(id=selected_variant_id)
                initial_variant = selected_variant_as_object
            except ProductVariant.DoesNotExist:
                pass # If invalid ID, just use the default.
        
        context['initial_variant'] = initial_variant

        # --- Review System Data ---
        context['reviews'] = product.reviews.all().order_by('-created_at')
        context['review_form'] = ReviewForm()
        
        # --- Purchase Verification for Reviews ---
        has_purchased = False
        if self.request.user.is_authenticated:
            has_purchased = Order.objects.filter(
                user=self.request.user,
                status__in=['delivered', 'shipped'],
                items__product_variant__product=product
            ).exists()
        context['has_purchased'] = has_purchased

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

# The @login_required decorator ensures that only authenticated users can access this page.
@login_required
def checkout(request):
    """
    Handles the entire checkout process, including:
    1. Displaying the address form and Stripe payment element (GET request).
    2. Creating a Stripe PaymentIntent to initiate the payment.
    3. Processing the address form and creating the Order in the database after
       a successful payment is confirmed on the frontend (POST request).
    4. Triggering an asynchronous task to send a confirmation email.
    """
    # Get the user's current cart from the session.
    cart = Cart(request)
    # Set the Stripe API secret key from our settings.
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # This block handles the form submission, which is now triggered by our frontend JavaScript
    # ONLY AFTER a successful payment confirmation from Stripe.
    if request.method == 'POST':
        # Create a form instance and populate it with the submitted data.
        form = OrderCreateForm(request.POST)
        
        # Check if the submitted address data is valid.
        if form.is_valid():
            # Save the form data to create a new Address object, but don't commit to the DB yet.
            address = form.save(commit=False)
            # Associate the new address with the currently logged-in user.
            address.user = request.user
            # Now, save the complete Address object to the database.
            address.save()

            # Create the main Order object in the database.
            order = Order.objects.create(
                user=request.user,
                shipping_address=address,
                total_amount=cart.get_total_price()
            )

            # Loop through every item in the cart to create individual OrderItem records.
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    product_variant=item['variant'],
                    price=item['price'],
                    quantity=item['quantity']
                )
            
            # The order is successfully created, so clear the user's cart from the session.
            cart.clear()

            # --- THIS IS THE NEW CELERY INTEGRATION ---
            # Instead of calling the email function directly and making the user wait,
            # we call .delay(). This sends the task (and the order ID) to our Celery queue.
            # A separate 'worker' process will pick up this job and execute it in the background.
            send_order_confirmation_email.delay(order.id)
            
            # Redirect the user to their profile page where they can see their new order.
            return redirect('store:profile')
    
    # This block handles the initial page load (GET request).
    else:
        # Create a blank instance of our address form.
        form = OrderCreateForm()
        intent = None # Initialize the payment intent as None.
        
        # Only attempt to create a Stripe PaymentIntent if the cart has items.
        if cart.get_total_price() > 0:
            try:
                # Create a PaymentIntent object on Stripe's servers.
                # This represents the payment session.
                intent = stripe.PaymentIntent.create(
                    amount=int(cart.get_total_price() * 100), # Amount must be in the smallest currency unit (kuruş).
                    currency='try',
                    automatic_payment_methods={'enabled': True},
                )
            except stripe.error.StripeError as e:
                # If Stripe returns an error (e.g., amount is too low), print it to the server console.
                print(f"Stripe Error: {e}")
        
    # Prepare the context dictionary to pass data to the template.
    context = {
        'cart': cart,
        'form': form,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        # The client_secret is the temporary key that authorizes the frontend
        # JavaScript to confirm this specific payment with Stripe.
        'client_secret': intent.client_secret if intent else None,
    }
    # Render the checkout page template with the prepared context.
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


@require_POST
def cart_update_api(request):
    """
    An API-like view to handle updating a cart item's quantity via AJAX.
    It expects a JSON POST request and returns a JSON response.
    """
    cart = Cart(request)
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        quantity = int(data.get('quantity'))

        if not variant_id or quantity < 1:
            return JsonResponse({'error': 'Invalid data'}, status=400)

        variant = get_object_or_404(ProductVariant, id=variant_id)
        cart.add(variant=variant, quantity=quantity, override_quantity=True)

        response_data = {
            'success': True,
            'cart_total_price': cart.get_total_price(),
            'cart_total_items': len(cart),
            'item_total_price': variant.sale_price * quantity,
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def cart_remove_api(request):
    """
    An API-like view to handle removing a cart item via AJAX.
    """
    cart = Cart(request)
    try:
        data = json.loads(request.body)
        variant_id = data.get('variant_id')

        if not variant_id:
            return JsonResponse({'error': 'Invalid data'}, status=400)

        variant = get_object_or_404(ProductVariant, id=variant_id)
        cart.remove(variant)

        response_data = {
            'success': True,
            'cart_total_price': cart.get_total_price(),
            'cart_total_items': len(cart),
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    