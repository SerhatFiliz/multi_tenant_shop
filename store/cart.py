# store/cart.py

from decimal import Decimal
from django.conf import settings
from .models import ProductVariant

class Cart:
    """
    Manages the shopping cart using the Django session framework.
    The cart is stored in the session as a dictionary:
    {
        'variant_id_1': {'quantity': X, 'price': 'Y.YY'},
        'variant_id_2': {'quantity': Z, 'price': 'W.WW'},
    }
    """

    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session if it doesn't exist
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, variant, quantity=1, override_quantity=False):
        """
        Add a product variant to the cart or update its quantity.
        """
        variant_id = str(variant.id)
        if variant_id not in self.cart:
            self.cart[variant_id] = {'quantity': 0, 'price': str(variant.sale_price)}
        
        if override_quantity:
            self.cart[variant_id]['quantity'] = quantity
        else:
            self.cart[variant_id]['quantity'] += quantity
        self.save()

    def save(self):
        """
        Mark the session as "modified" to make sure it gets saved.
        """
        self.session.modified = True

    def remove(self, variant):
        """
        Remove a product variant from the cart.
        """
        variant_id = str(variant.id)
        if variant_id in self.cart:
            del self.cart[variant_id]
            self.save()

    def __iter__(self):
        """
        Loop through cart items and get the variants from the database.
        This allows us to use `for item in cart:` in our templates.
        """
        variant_ids = self.cart.keys()
        # Get the variant objects and add them to the cart
        variants = ProductVariant.objects.filter(id__in=variant_ids)
        cart = self.cart.copy()
        for variant in variants:
            cart[str(variant.id)]['variant'] = variant

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate the total cost of the items in the cart.
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """
        Remove the cart from the session.
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()