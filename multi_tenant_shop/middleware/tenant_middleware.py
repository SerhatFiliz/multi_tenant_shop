# multi_tenant_shop/middleware/tenant_middleware.py
from django.http import HttpResponseForbidden
from django_tenants.middleware.main import TenantMainMiddleware
from django_tenants.utils import get_tenant_model

class CustomTenantMiddleware(TenantMainMiddleware):
    def process_request(self, request):
        """
        Processes the request to set the correct tenant and checks for approval.
        """
        # Call the parent class's method to handle schema switching
        super().process_request(request)

        # Skip the check for the public schema
        if request.tenant.schema_name == 'public':
            return None

        # Check if the tenant is approved
        if not request.tenant.is_approved:
            return HttpResponseForbidden("This store is not yet active. Please check back later.")
            
        return None