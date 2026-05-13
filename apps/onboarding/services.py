from __future__ import annotations

import secrets

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils.text import slugify
from django_tenants.utils import schema_context

from store.models import Domain, StoreSettings, Tenant, TenantInvitation


class TenantOnboardingService:
    """Creates a tenant schema, domains, and the first StoreManager."""

    @staticmethod
    def provision_store(*, store_name: str, first_name: str, last_name: str, email: str, password: str) -> Tenant:
        schema_name = slugify(store_name).replace("-", "")[:50]
        subdomain = slugify(store_name)[:63]
        if not schema_name:
            raise ValueError("Store name must contain at least one letter or number.")

        with transaction.atomic():
            tenant = Tenant.objects.create(
                schema_name=schema_name,
                name=store_name,
                subdomain=subdomain,
                is_approved=True,
            )
            Domain.objects.create(tenant=tenant, domain=f"{subdomain}.nexus.com", is_primary=True)
            Domain.objects.create(tenant=tenant, domain=f"{subdomain}.localhost", is_primary=False)

        User = get_user_model()
        with schema_context(tenant.schema_name):
            manager = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                tenant_role=User.ROLE_ADMIN,
                is_staff=True,
            )
            StoreSettings.objects.get_or_create(defaults={"target_profit_margin": tenant.target_profit_margin})

        tenant.owner = manager
        tenant.save(update_fields=["owner"])
        return tenant


class TenantInvitationService:
    """Handles StoreManager team invitations."""

    @staticmethod
    def invite_user(*, email: str, role: str, invited_by) -> TenantInvitation:
        invitation = TenantInvitation.objects.create(
            email=email,
            role=role,
            invited_by=invited_by,
            token=secrets.token_urlsafe(32),
        )
        send_mail(
            "You have been invited to NexusCommerce",
            f"You were invited as {role}. Invite token: {invitation.token}",
            "no-reply@nexus.com",
            [email],
            fail_silently=True,
        )
        return invitation


def provision_tenant_store(**kwargs) -> Tenant:
    return TenantOnboardingService.provision_store(**kwargs)


def invite_tenant_user(**kwargs) -> TenantInvitation:
    return TenantInvitationService.invite_user(**kwargs)

