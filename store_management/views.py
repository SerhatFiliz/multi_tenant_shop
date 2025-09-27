# multi_tenant_shop/store_management/views.py
from django.shortcuts import render, redirect
from django.views.generic import FormView, TemplateView
from django.contrib import messages
from store.models import Tenant, Domain
from .forms import TenantCreationForm
from django.views.generic.edit import FormView

class TenantCreateView(FormView):
    """
    A view to handle the creation of a new store (tenant).
    The store will be created with `is_approved=False` by default.
    """
    template_name = 'store_management/tenant_create.html'
    form_class = TenantCreationForm
    success_url = '/'  # Redirect to the public homepage after submission

    def form_valid(self, form):
        # Create the tenant instance
        tenant = form.save(commit=False)
        tenant.owner = self.request.user  # Assuming a logged-in user is the owner
        tenant.is_approved = False  # Set to False by default, requires admin approval
        tenant.save()

        # Create the domain for the new tenant
        domain = Domain.objects.create(
            tenant=tenant, 
            domain=f"{tenant.schema_name}.localhost", # Example domain structure
            is_primary=True
        )

        messages.success(self.request, "Your store creation request has been submitted. It will be active after admin approval.")
        return super().form_valid(form)
    
class HomeView(TemplateView):
    template_name = "store_management/home.html"
    
class DashboardView(TemplateView):
    template_name = "store_management/dashboard.html" 