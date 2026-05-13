# store/context_processors.py
import os
from django.conf import settings
from .cart import Cart

def tenant_context(request):
    """
    Makes the current tenant, cart, and AI service port available in every
    template. The AI port is read from the AI_PORT environment variable
    which is dynamically set by master_launcher.py at boot time.
    """
    return {
        'current_tenant': request.tenant,
        'cart': Cart(request),
        # The FastAPI SaaS Brain port, injected by master_launcher.py.
        # Used by base.html to construct the KOBI-AI widget src URL.
        'ai_port': os.getenv('AI_PORT', '8002'),
        'ai_service_base_url': getattr(settings, 'AI_SERVICE_BASE_URL', 'http://127.0.0.1:8002'),
    }
