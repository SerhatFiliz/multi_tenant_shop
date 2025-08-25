# store/tests.py

# Import Django's TestCase class, which provides a great foundation for database tests.
from django.test import TestCase, RequestFactory
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware

# Import the models and classes we need to test.
from .models import Tenant, Domain, Product, Category, ProductVariant
from .cart import Cart

class CartTestCase(TestCase):
    """
    This class will contain all the unit tests for our Cart functionality.
    It inherits from TestCase, which means it will run inside a transaction
    and have its own temporary, clean database for each test.
    """

    def setUp(self):
        """
        The setUp method is a special method that runs BEFORE each test method in this class.
        We use it to create any objects that will be needed across multiple tests.
        """
        # We need a RequestFactory to create mock request objects.
        self.factory = RequestFactory()

        # Create the necessary objects for a product to exist.
        self.category = Category.objects.create(name='Test Kategori', slug='test-kategori')
        self.product = Product.objects.create(name='Test Ürün', slug='test-urun', category=self.category)
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='TEST-SKU-01',
            color='Test Rengi',
            sale_price=10.00,
            stock_quantity=100
        )

    def _get_request_with_session(self):
        """
        A helper method to create a request object with a functioning session,
        which is required for our Cart to work.
        """
        request = self.factory.get('/')
        # The session middleware is needed to create request.session
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_add_item_to_cart(self):
        """
        This is our first test. It checks if we can successfully add an item to an empty cart.
        Test method names MUST start with 'test_'.
        """
        # 1. ARRANGE: Set up the scenario for the test.
        request = self._get_request_with_session()
        cart = Cart(request)

        # 2. ACT: Perform the action we want to test.
        cart.add(variant=self.variant, quantity=2)

        # 3. ASSERT: Check if the outcome is what we expected.
        # self.assertEqual(expected_value, actual_value)
        self.assertEqual(len(cart), 2) # Check if the total quantity in the cart is 2.
        self.assertEqual(cart.get_total_price(), 20.00) # Check if the total price is correct (2 * 10.00).
        
        # Check if the variant ID is present as a key in the cart's session data.
        self.assertIn(str(self.variant.id), cart.cart)
        # Check if the quantity for that specific item is correct.
        self.assertEqual(cart.cart[str(self.variant.id)]['quantity'], 2)
        
        print("\n✅ test_add_item_to_cart PASSED")

    def test_update_item_quantity_in_cart(self):
        """
        This test checks if we can update the quantity of an item already in the cart.
        """
        # 1. ARRANGE
        request = self._get_request_with_session()
        cart = Cart(request)
        cart.add(variant=self.variant, quantity=1) # Start with 1 item in the cart.

        # 2. ACT
        # Call the add method again, but this time with override_quantity=True
        cart.add(variant=self.variant, quantity=5, override_quantity=True)

        # 3. ASSERT
        self.assertEqual(len(cart), 5) # The total quantity should now be 5, not 6.
        self.assertEqual(cart.get_total_price(), 50.00)
        self.assertEqual(cart.cart[str(self.variant.id)]['quantity'], 5)

        print("✅ test_update_item_quantity_in_cart PASSED")

    def test_remove_item_from_cart(self):
        """
        This test checks if we can successfully remove an item from the cart.
        """
        # 1. ARRANGE
        request = self._get_request_with_session()
        cart = Cart(request)
        cart.add(variant=self.variant, quantity=3)

        # 2. ACT
        cart.remove(variant=self.variant)

        # 3. ASSERT
        self.assertEqual(len(cart), 0) # The cart should be empty.
        self.assertNotIn(str(self.variant.id), cart.cart) # The variant ID should no longer be a key.
        self.assertEqual(cart.get_total_price(), 0.00)

        print("✅ test_remove_item_from_cart PASSED")