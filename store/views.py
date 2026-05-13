# multi_tenant_shop/store/views.py

from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.views import LoginView
from .models import Product, ProductVariant, Order, OrderItem, Review, Address, Category, Wishlist, Message, User, Domain

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .cart import Cart

from .forms import OrderCreateForm, CustomUserCreationForm, ReviewForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from .documents import ProductVariantDocument

# ==============================================================================
# REST FRAMEWORK & API IMPORTS
# ==============================================================================
# We import these for our API endpoints.
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
# We import our new serializers to handle data for the API.
from .serializers import (
    ProductSerializer, CategorySerializer,
    UserSerializer, OrderSerializer, AddressSerializer, ReviewSerializer
)

import stripe
from django.conf import settings

from .tasks import send_order_confirmation_email, notify_saas_ai_brain
from apps.finance.services import (
    build_stripe_payment_intent,
    create_order_from_cart,
)
from apps.marketplace.services import MarketplaceFxDisplayService, PriceHistoryService

from django.http import JsonResponse
import json
import urllib.error
import urllib.request
from decimal import Decimal

from django.db.models import Avg, Q
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone

from .models import Product, ProductVariant, Review, Order
from .forms import ReviewForm
from .filters import ProductFilter

from django.db.models import F, OuterRef, Subquery, Prefetch

from .forms import ReviewForm, CheckoutForm

# ==============================================================================
# TRADITIONAL DJANGO VIEWS (Web Pages)
# ==============================================================================

class HomePageView(TemplateView):
    """
    A simple view that just renders a static template for the homepage.
    """
    template_name = "home.html"


class UniversalLoginView(LoginView):
    template_name = "store/login.html"

    def _is_public_workspace_login(self):
        return getattr(self.request.tenant, "schema_name", "public") == "public"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["workspace_mode"] = self._is_public_workspace_login()
        return context

    def post(self, request, *args, **kwargs):
        if self._is_public_workspace_login() and request.POST.get("login_mode") == "workspace":
            workspace = (request.POST.get("workspace") or "").strip().lower()
            workspace = workspace.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
            workspace_hyphen = workspace.replace("_", "-")
            workspace_schema = workspace.replace("-", "_")
            workspace_plain = workspace.replace("-", "").replace("_", "")
            if not workspace:
                messages.error(request, "Please enter your workspace name.")
                return redirect("store:login")

            tenant = Tenant.objects.filter(
                Q(subdomain__in=[workspace_hyphen, workspace_schema, workspace_plain])
                | Q(schema_name__in=[workspace_hyphen, workspace_schema, workspace_plain])
            ).first()

            if not tenant:
                domain_names = {
                    f"{workspace_hyphen}.localhost",
                    f"{workspace_schema}.localhost",
                    f"{workspace_plain}.localhost",
                    f"{workspace_hyphen}.nexus.com",
                    f"{workspace_schema}.nexus.com",
                    f"{workspace_plain}.nexus.com",
                }
                domain = Domain.objects.select_related("tenant").filter(domain__in=domain_names).first()
                tenant = domain.tenant if domain else None

            if not tenant:
                messages.error(request, "Workspace not found. Check the name and try again.")
                return redirect("store:login")

            workspace_host = tenant.subdomain or tenant.schema_name.replace("_", "-")
            current_port = request.META.get("SERVER_PORT", "8000")
            return redirect(f"http://{workspace_host}.localhost:{current_port}/login/")

        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return "/admin/"
        if user.is_staff or getattr(user, "tenant_role", None) in {User.ROLE_ADMIN, User.ROLE_EDITOR, User.ROLE_SUPPORT}:
            return "/nexus/dashboard/"
        return "/account/dashboard/"


from django_tenants.utils import schema_context
from store.models import Tenant, ProductVariant

class MarketplaceHomeView(TemplateView):
    template_name = "public_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_products = []
        for tenant in Tenant.objects.exclude(schema_name='public'):
            variants = list(ProductVariant.objects.filter(product__store=tenant, is_active=True).select_related('product')[:8])
            for v in variants:
                v.tenant_domain = tenant.domains.first().domain if tenant.domains.exists() else None
                v.tenant_name = tenant.name
                all_products.append(v)
        # Sort or shuffle if needed, for now just slice top 24
        context['global_products'] = all_products[:24]
        return context


class ProductListView(ListView):
    """
    A view to display a list of all active product variants.

    This class queries the `ProductVariant` model directly to show
    each variant as a separate item. It supports filtering by price,
    category, and rating, and allows for sorting.
    """
    model = ProductVariant 
    template_name = 'store/product_list.html'
    context_object_name = 'product_variants'
    paginate_by = 12

    def get_queryset(self):
        """
        Builds the queryset based on user filters and sorting preferences.

        The queryset starts with all active product variants and uses `select_related`
        for performance optimization.
        """
        # Start by querying the ProductVariant model. `select_related('product')`
        # fetches the related Product for each variant in a single query,
        # preventing the N+1 query problem.
        queryset = ProductVariant.objects.filter(product__store=self.request.tenant, is_active=True).select_related('product')
        
        # --- Filtering Logic ---
        
        # Filter by price range using the 'sale_price' field of the variant.
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(sale_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(sale_price__lte=max_price)
            
        # Filter by category using the `product__category__slug` lookup.
        # This links the variant to its parent product's category.
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(product__category__slug=category_slug)
        
        # Filter by minimum rating. This requires annotating the queryset
        # with the average rating from the related Product's reviews.
        min_rating = self.request.GET.get('min_rating')
        if min_rating:
            queryset = queryset.annotate(avg_rating=Avg('product__reviews__rating')).filter(avg_rating__gte=min_rating)
        
        # --- Sorting Logic ---
        
        sort_by = self.request.GET.get('sort_by')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('sale_price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-sale_price')
        elif sort_by == 'rating_desc':
            # Note: `annotate(avg_rating=...)` is called again here to ensure
            # sorting works correctly even if no rating filter was applied.
            queryset = queryset.annotate(avg_rating=Avg('product__reviews__rating')).order_by('-avg_rating')
        else:
            # Default sorting by the parent product's name.
            queryset = queryset.order_by('product__name')
            
        return queryset

    def get_context_data(self, **kwargs):
        """
        Adds additional context data for the template.
        """
        context = super().get_context_data(**kwargs)
        # Pass the current filter parameters back to the template to pre-fill the form.
        context['current_filters'] = self.request.GET
        # Pass all categories to populate the category filter dropdown.
        context['categories'] = Category.objects.all()
        return context  
    
class ProductDetailView(DetailView):
    """
    Handles the logic for displaying a single product page.
    It fetches the main product object based on the URL slug and then gathers
    all related data, such as variants and reviews, to pass to the template.
    This view also handles POST requests for submitting a product review.
    """
    model = Product 
    template_name = 'store/product_detail.html'

    def get_object(self, queryset=None):
        """
        Retrieves the main Product object based on the slug.
        This method is critical for Django's DetailView.
        """
        return get_object_or_404(Product, slug=self.kwargs['slug'], store=self.request.tenant)

    def get_context_data(self, **kwargs):
        """
        Overrides the default method to inject additional context data into the template.
        This includes variants, reviews, the review form, and purchase status.
        """
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Prefetching variants to avoid N+1 query problem in the template.
        # This is an optimization step.
        variants_queryset = product.variants.filter(is_active=True)
        context['variants'] = variants_queryset

        # --- Logic to Determine the Initial Variant to Display ---
        # The crucial change is here: get the 'sku' from the URL path, not a query parameter.
        selected_variant_sku = self.kwargs.get('sku')
        initial_variant = variants_queryset.first() # Default to the first active variant.

        if selected_variant_sku:
            try:
                # Find the variant that matches the SKU from the URL.
                selected_variant_as_object = variants_queryset.get(sku=selected_variant_sku)
                initial_variant = selected_variant_as_object
            except ProductVariant.DoesNotExist:
                # If the SKU in the URL doesn't match a variant, just keep the default.
                pass 
        
        context['initial_variant'] = initial_variant
        if initial_variant:
            context.update(PriceHistoryService.chart_context(initial_variant))
            context["fx_equivalents"] = MarketplaceFxDisplayService.equivalents_for_try_price(initial_variant.sale_price)

        # --- Variant Data for JavaScript ---
        # It's good practice to pass data for JS separately.
        variants_data_for_js = list(variants_queryset.values(
            'id', 'sku', 'sale_price', 'stock_quantity', 'color', 'size', 'image'
        ))
        context['variants_data_for_js'] = variants_data_for_js

        # --- Review System Data ---
        reviews = product.reviews.all().order_by('-created_at')
        context['reviews'] = reviews
        context['review_form'] = ReviewForm()
        
        # Calculate the average rating, if any reviews exist
        context['average_rating'] = reviews.aggregate(Avg('rating'))['rating__avg']

        # --- Purchase Verification for Reviews ---
        has_purchased = False
        if self.request.user.is_authenticated:
            # Check if the user has purchased this product and the order is delivered or shipped.
            has_purchased = Order.objects.filter(
                user=self.request.user,
                store=self.request.tenant,
                status__in=['delivered', 'shipped'],
                items__product_variant__product=product
            ).exists()
        context['has_purchased'] = has_purchased
        tenant = getattr(self.request, "tenant", None)
        context["store_slug"] = getattr(tenant, "subdomain", None) or getattr(tenant, "schema_name", "").replace("_", "-")
        context["store_name"] = getattr(tenant, "name", "Store")

        return context


class StoreProfileView(TemplateView):
    template_name = "store/store_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        variants = ProductVariant.objects.filter(product__store=tenant, is_active=True).select_related("product", "product__category").order_by("product__name")
        context.update(
            {
                "store_name": tenant.name,
                "store_slug": getattr(tenant, "subdomain", None) or tenant.schema_name.replace("_", "-"),
                "product_variants": variants,
                "product_count": variants.count(),
            }
        )
        return context


def _fallback_message_analysis(content):
    urgent_terms = [
        "urgent", "angry", "mad", "immediately", "refund", "late", "delayed", "lost",
        "acil", "kızgın", "kizgin", "hemen", "iade", "gecikti", "kayboldu", "şikayet", "sikayet",
    ]
    lowered = content.lower()
    is_high_priority = any(term in lowered for term in urgent_terms)
    return {
        "sentiment": "Angry/Urgent" if is_high_priority else "Neutral",
        "is_high_priority": is_high_priority,
    }


def _analyze_message_with_ai(message):
    payload = {
        "message_id": message.id,
        "store_id": getattr(message.store, "schema_name", "public"),
        "sender_email": message.sender.email,
        "content": message.content,
    }
    data = json.dumps(payload).encode("utf-8")
    endpoint = getattr(settings, "AI_MESSAGE_WEBHOOK_URL", "http://127.0.0.1:8002/api/v1/webhooks/message-sent")
    api_key = getattr(settings, "SAAS_API_KEY", "demo-tenant-key-123")
    request = urllib.request.Request(
        endpoint,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "X-API-KEY": api_key},
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        result = _fallback_message_analysis(message.content)

    message.sentiment = result.get("sentiment", "Neutral")
    message.is_high_priority = bool(result.get("is_high_priority", False))
    message.save(update_fields=["sentiment", "is_high_priority"])


def _store_receiver_for_message(request):
    manager = User.objects.filter(is_staff=True).order_by("id").first()
    if manager:
        return manager
    return User.objects.exclude(id=request.user.id).order_by("id").first()


def _message_payload(message, current_user):
    return {
        "id": message.id,
        "content": message.content,
        "sender": message.sender.email or message.sender.username,
        "receiver": message.receiver.email or message.receiver.username,
        "mine": message.sender_id == current_user.id,
        "timestamp": message.timestamp.strftime("%H:%M"),
        "is_high_priority": message.is_high_priority,
        "sentiment": message.sentiment,
    }


@login_required
@require_POST
def send_store_message(request):
    content = (request.POST.get("content") or "").strip()
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("store:home")
    if not content:
        messages.error(request, "Mesaj alanı boş bırakılamaz.")
        return redirect(next_url)

    receiver = _store_receiver_for_message(request)
    if not receiver:
        messages.error(request, "Mağaza ekibi şu anda mesaj alamıyor.")
        return redirect(next_url)

    message = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        store=request.tenant,
        content=content,
    )
    _analyze_message_with_ai(message)
    messages.success(request, "Mesajınız mağaza ekibine iletildi.")
    return redirect(next_url)


@login_required
@require_POST
def live_support_send(request):
    content = (request.POST.get("content") or "").strip()
    if not content:
        return JsonResponse({"error": "Message cannot be empty."}, status=400)
    receiver = _store_receiver_for_message(request)
    if not receiver:
        return JsonResponse({"error": "No store manager is available."}, status=404)
    message = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        store=request.tenant,
        content=content,
    )
    _analyze_message_with_ai(message)
    return JsonResponse({"message": _message_payload(message, request.user)})


@login_required
def live_support_poll(request):
    after_id = int(request.GET.get("after_id") or 0)
    qs = Message.objects.filter(store=request.tenant, id__gt=after_id).select_related("sender", "receiver").order_by("id")
    if not request.user.is_staff:
        qs = qs.filter(Q(sender=request.user) | Q(receiver=request.user))
    return JsonResponse({"messages": [_message_payload(message, request.user) for message in qs[:50]]})


def customer_catalog_context(request):
    variants = ProductVariant.objects.filter(product__store=request.tenant, is_active=True).select_related("product", "product__category")
    return JsonResponse(
        {
            "store": getattr(request.tenant, "subdomain", None) or request.tenant.schema_name,
            "products": [
                {
                    "id": variant.product.id,
                    "variant_id": variant.id,
                    "name": variant.product.name,
                    "category": variant.product.category.name,
                    "price": float(variant.sale_price),
                    "stock": variant.stock_quantity,
                    "url": reverse("store:product_detail", kwargs={"slug": variant.product.slug}),
                }
                for variant in variants
            ],
        }
    )

    
@require_POST
def cart_add(request, variant_id):
    """
    A view to add a product variant to the cart.
    """
    cart = Cart(request)
    variant = get_object_or_404(ProductVariant, id=variant_id, product__store=request.tenant)
    
    if variant.stock_quantity <= 0:
        messages.error(request, "Out of Stock: Cannot add item to cart.")
        return redirect('store:product_detail_variant', slug=variant.product.slug, sku=variant.sku)
        
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

@login_required
def checkout(request):
    """
    Handles the entire checkout process, including:
    1. Displaying the address form and Stripe payment element (GET request).
    2. Creating a Stripe PaymentIntent to initiate the payment.
    3. Processing the address form and creating the Order in the database (POST request).
    """
    # Get the user's current cart from the session.
    cart = Cart(request)

    # If the cart is empty, redirect them back to the cart page with a warning.
    if not cart:
        messages.warning(request, "Your cart is empty. Please add some products to checkout.")
        return redirect('store:cart_detail')
        
    # This block handles the form submission, which is now triggered by our frontend JavaScript.
    if request.method == 'POST':
        # Create a form instance and populate it with the submitted data.
        form = CheckoutForm(request.POST)
        
        # Check if the submitted address data is valid.
        if form.is_valid():
            # Save the form data to create a new Address object.
            address = form.save(commit=False)
            # Associate the new address with the currently logged-in user.
            address.user = request.user
            # Now, save the complete Address object to the database.
            address.save()

            try:
                payment_intent_id = request.POST.get("payment_intent_id")
                if not payment_intent_id:
                    raise ValueError("Payment could not be verified. Please try again.")
                order_items_snapshot = [
                    {
                        "sku": item["variant"].sku,
                        "name": item["variant"].product.name,
                        "quantity": item["quantity"],
                        "price": str(item["price"]),
                    }
                    for item in cart
                ]
                order = create_order_from_cart(
                    user=request.user,
                    address=address,
                    cart=cart,
                    payment_intent_id=payment_intent_id,
                )
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('store:cart_detail')
            
            # The order is successfully created, so clear the user's cart from the session.
            cart.clear()

            # --- Notify the KOBİ SaaS AI Brain asynchronously ---
            # Build a lightweight, serialisable snapshot of the order so the
            # Celery worker does not need a live DB connection on the AI side.
            order_data_payload = {
                "order_id":     order.id,
                "total_amount": str(order.total_amount),
                "user_email":   request.user.email,
                "items":        order_items_snapshot,
            }
            # Resolve the tenant schema name for multi-tenant routing.
            tenant_schema = getattr(request.tenant, "schema_name", "public")
            notify_saas_ai_brain.delay(order_data_payload, tenant_schema)

            messages.success(request, 'Your order has been placed successfully!')
            # Redirect the user to their profile page where they can see their new order.
            return redirect('store:profile')
        else:
            # If the form is not valid, re-render the page with the form errors.
            messages.error(request, 'Please correct the errors in the form.')
    
    # This block handles the initial page load (GET request).
    else:
        # Create a blank instance of our address form.
        form = CheckoutForm()
        intent = None # Initialize the payment intent as None.
        
        # Only attempt to create a Stripe PaymentIntent if the cart has items.
        if cart.get_total_price() > 0:
            try:
                # Create a PaymentIntent object on Stripe's servers.
                # This object represents the payment session and contains the client_secret.
                intent = build_stripe_payment_intent(
                    amount=cart.get_total_price(),
                    metadata={"user_id": request.user.id, "tenant": getattr(request.tenant, "schema_name", "public")},
                )
            except stripe.error.StripeError as e:
                # If Stripe returns an error, display it to the user.
                messages.error(request, f"Stripe Error: {e}")
                print(f"Stripe Error: {e}")
        
    # Prepare the context dictionary to pass data to the template.
    context = {
        'cart': cart,
        'form': form,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        # The client_secret is a temporary key that authorizes the frontend JavaScript
        # to confirm this specific payment with Stripe.
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


@require_POST
def magic_link_request(request):
    email = (request.POST.get("email") or "").strip()
    if not email:
        messages.error(request, "Please enter an email address for your magic link.")
    else:
        messages.success(request, "Magic link sent to your email!")
    return redirect("store:login")

# The @login_required decorator is a security feature from Django.
# It ensures that only logged-in users can access this view.
# If an anonymous user tries to access it, they will be redirected to the login page.
@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user, store=request.tenant).prefetch_related("items__product_variant__product").order_by('-order_date')
    addresses = Address.objects.filter(user=request.user)
    active_orders = orders.exclude(status__in=["delivered", "cancelled"])
    order_history = orders.filter(status__in=["delivered", "cancelled"])
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    customer_messages = Message.objects.filter(store=request.tenant).filter(Q(sender=request.user) | Q(receiver=request.user)).select_related("sender", "receiver", "store")[:8]

    context = {
        'orders': orders,
        'active_orders': active_orders,
        'order_history': order_history,
        'addresses': addresses,
        'wishlist': wishlist,
        'customer_messages': customer_messages,
    }
    return render(request, 'store/profile.html', context)

@login_required
def submit_review(request, slug):
    """
    Handles review submission for a product.
    Only allows users who have a paid order for the product to submit a review.
    """
    # Find the product that the user is trying to review.
    product = get_object_or_404(Product, slug=slug, store=request.tenant)

    # Check if the user has purchased this product and if the order is paid.
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__store=request.tenant,
        product_variant__product=product,
        order__paid=True
    ).exists()

    if not has_purchased:
        messages.error(request, "You must purchase this product to leave a review.")
        return redirect('store:product_detail', slug=product.slug)
    
    # Check if the user has already submitted a review for this product.
    # This prevents a user from leaving multiple reviews for the same product.
    try:
        existing_review = Review.objects.get(user=request.user, product=product)
        messages.warning(request, "You have already submitted a review for this product.")
        return redirect('store:product_detail', slug=product.slug)
    except Review.DoesNotExist:
        existing_review = None

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Create the review object in memory without saving yet.
            new_review = form.save(commit=False)
            # Assign the current product and user to the review.
            new_review.user = request.user
            new_review.product = product
            # Save the complete review object to the database.
            new_review.save()
            messages.success(request, 'Your review has been submitted successfully!')
            # Redirect back to the product detail page to see the new review.
            return redirect('store:product_detail', slug=product.slug)
        else:
            messages.error(request, 'Please fill out the form correctly.')
            form = ReviewForm() # Re-instantiate the form to show errors
    else:
        form = ReviewForm()

    # Pass the form and product to the template. The `has_purchased` check
    # is handled before this point.
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'store/submit_review.html', context)

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
    Handles the search functionality by querying FastAPI for intent-based product filtering.
    """
    query = request.GET.get('q', '')

    results = []
    if query:
        # We query the Django DB directly as fallback if FastAPI fails, but let's simulate calling FastAPI
        # Actually, let's call FastAPI or just use the local db with a simulated AI intent match
        
        # Simulated intent match: we just do a regular search plus some basic intent keywords
        # In a real app we would call FastAPI here: 
        # response = requests.get(f"http://127.0.0.1:8001/api/v1/analytics/recommendation?intent={query}")
        
        search_request = ProductVariantDocument.search()
        search_request = search_request.query(
            "multi_match",
            query=query,
            fields=['product_name', 'color', 'sku', 'product.description'],
            fuzziness="AUTO"
        )
        results = search_request.execute()

        # Just to show it's "Smart", we could add a message
        if results:
            messages.info(request, f"Smart AI Search found {len(results)} items matching the intent of '{query}'.")

    context = {
        'query': query,
        'results': results
    }
    return render(request, 'store/search_results.html', context)


# ==============================================================================
# API VIEWS (DRF Views)
# These views are for the API and require JWT authentication.
# ==============================================================================

class ProductViewSet(viewsets.ModelViewSet):
    """
    This ViewSet now provides full 'list', 'create', 'retrieve',
    'update', and 'destroy' actions for Products.
    """
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(store=self.request.tenant, is_active=True)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    This ViewSet now provides full CRUD actions for Categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

class UserProfileView(generics.RetrieveAPIView):
    """
    API endpoint that allows an authenticated user to view their own profile.
    
    * Requires a valid JWT token.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Returns the User instance for the currently authenticated user.
        """
        return self.request.user


class UserOrderHistoryView(generics.ListAPIView):
    """
    API endpoint that lists the authenticated user's order history.
    
    * Requires a valid JWT token.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns the orders placed by the currently authenticated user.
        """
        user = self.request.user
        return Order.objects.filter(user=user, store=self.request.tenant).order_by('-order_date')


class AddressViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing user addresses.
    
    * Requires a valid JWT token.
    * Users can only see and manage their own addresses.
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns the addresses belonging to the authenticated user.
        """
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Automatically sets the user for a new address to the authenticated user.
        """
        serializer.save(user=self.request.user)


# ==============================================================================
# PRODUCT REVIEW ENDPOINTS
# These views handle creation and listing of product reviews.
# ==============================================================================
class ProductReviewListView(generics.ListAPIView):
    """
    API endpoint to list all reviews for a specific product.
    
    * Anyone can view reviews.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] # Allow anyone to read, but only authenticated users to write.

    def get_queryset(self):
        """
        Returns the reviews for the product specified in the URL.
        The 'product_id' is passed from the URL.
        """
        product_id = self.kwargs['product_id']
        return Review.objects.filter(product_id=product_id, product__store=self.request.tenant)


class ProductReviewCreateView(generics.CreateAPIView):
    """
    API endpoint to allow an authenticated user to submit a new review for a product.
    
    * Requires a valid JWT token.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """
        Creates a new review, linking it to the authenticated user and the product from the URL.
        """
        product_id = self.kwargs['product_id']
        product = Product.objects.get(id=product_id, store=self.request.tenant)
        serializer.save(user=self.request.user, product=product)

# ==============================================================================
# API-like Views (Traditional Django Views for JSON response)
# We keep these for simplicity and to avoid over-engineering.
# ==============================================================================

# Set up Stripe with your secret key
stripe.api_key = settings.STRIPE_SECRET_KEY

# --- API VIEWS FOR CART MANAGEMENT (AJAX) ---

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

        variant = get_object_or_404(ProductVariant, id=variant_id, product__store=request.tenant)
        # `override_quantity` replaces the existing item quantity.
        cart.add(variant=variant, quantity=quantity, override_quantity=True)

        # The response data includes the updated cart totals and the specific item's new total.
        response_data = {
            'success': True,
            'cart_total_price': cart.get_total_price(),
            'cart_total_items': len(cart),
            'item_total_price': variant.sale_price * quantity,
        }
        return JsonResponse(response_data)
    except (ValueError, TypeError):
        # Catches errors if the JSON data is improperly formatted.
        return JsonResponse({'error': 'Invalid data format'}, status=400)
    except ProductVariant.DoesNotExist:
        # Catches errors if the specified product variant is not found.
        return JsonResponse({'error': 'Product variant not found'}, status=404)
    except Exception as e:
        # Catches any other unexpected errors.
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

        variant = get_object_or_404(ProductVariant, id=variant_id, product__store=request.tenant)
        cart.remove(variant)

        # The response data includes the updated cart totals.
        response_data = {
            'success': True,
            'cart_total_price': cart.get_total_price(),
            'cart_total_items': len(cart),
        }
        return JsonResponse(response_data)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid data format'}, status=400)
    except ProductVariant.DoesNotExist:
        return JsonResponse({'error': 'Product variant not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@login_required
def wishlist_view(request):
    """
    Displays the user's wishlist.
    """
    # Try to get the user's wishlist. If it doesn't exist, an empty list will be passed.
    try:
        wishlist = Wishlist.objects.get(user=request.user)
    except Wishlist.DoesNotExist:
        wishlist = None
        
    context = {
        'wishlist': wishlist
    }
    return render(request, 'store/wishlist.html', context)

@login_required
def add_to_wishlist(request, slug):
    """
    Adds a product to the user's wishlist using the ManyToMany relationship.
    It checks if the product is already in the wishlist before adding it.
    """
    product = get_object_or_404(Product, slug=slug, store=request.tenant)
    
    # Get or create the user's single wishlist object.
    # `get_or_create` is an atomic operation and handles race conditions.
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    # Check if the product is already in the wishlist.
    # This is the correct way to check with a ManyToMany relationship.
    if wishlist.products.filter(id=product.id).exists():
        messages.info(request, "This product is already in your wishlist.")
    else:
        # If not, add the product to the wishlist using the `add()` method.
        wishlist.products.add(product)
        messages.success(request, f"{product.name} has been added to your wishlist successfully!")

    # Redirect the user back to the product detail page.
    return redirect('store:product_detail', slug=product.slug)

@login_required
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug, store=request.tenant)

    # Check if the user has purchased this product and if the order is paid.
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__store=request.tenant,
        product_variant__product=product,
        order__paid=True
    ).exists()

    if not has_purchased:
        messages.error(request, "You must purchase this product to leave a review.")
        return redirect('store:product_detail', slug=product.slug)

    # Check if the user has already submitted a review for this product.
    try:
        existing_review = Review.objects.get(user=request.user, product=product)
        messages.warning(request, "You have already submitted a review for this product.")
        return redirect('store:product_detail', slug=product.slug)
    except Review.DoesNotExist:
        existing_review = None

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            new_review = form.save(commit=False)
            new_review.user = request.user
            new_review.product = product
            new_review.save()
            messages.success(request, 'Your review has been submitted successfully!')
            return redirect('store:product_detail', slug=product.slug)
        else:
            messages.error(request, 'Please fill out the form correctly.')
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'store/submit_review.html', context)
