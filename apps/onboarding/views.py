from __future__ import annotations

from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import FormView

from apps.onboarding.services import TenantOnboardingService
from store.forms import SelfServiceRegistrationForm


class PublicRegisterView(FormView):
    template_name = "store/register.html"
    form_class = SelfServiceRegistrationForm

    def form_valid(self, form):
        try:
            tenant = TenantOnboardingService.provision_store(
                store_name=form.cleaned_data["store_name"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
        except Exception as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f"Store provisioned. Login at https://{tenant.subdomain}.nexus.com/login/")
        return redirect("store_management:login")

