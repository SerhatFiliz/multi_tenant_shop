# store/context_processors.py
from .cart import Cart

def tenant_context(request):
    """
    This context processor makes the current tenant object available
    in every template across the entire project.
    The django-tenants middleware already adds the 'tenant' object
    to the incoming 'request' object. We are just extracting it here.
    """
    return {
        'current_tenant': request.tenant,
        'cart': Cart(request)
    }

