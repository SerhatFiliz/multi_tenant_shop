from django import forms
from django_tenants.utils import get_tenant_model
from django.contrib.auth import get_user_model
from django.db import connection

class TenantCreationForm(forms.ModelForm):
    first_name = forms.CharField(label="İsim", max_length=100)
    last_name = forms.CharField(label="Soyisim", max_length=100)
    email = forms.EmailField(label="E-posta", max_length=100)

    password = forms.CharField(widget=forms.PasswordInput, label="Şifre")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Şifre Tekrar")

    class Meta:
        model = get_tenant_model()
        fields = ('name',)
        labels = {
            'name': 'Mağaza Adı (Alan adı olarak kullanılacak)',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Şifreler eşleşmiyor.")

        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data['name'].lower()
        if not name.isalnum():
            raise forms.ValidationError("Mağaza adı sadece harf ve rakam içerebilir.")

        # Check if the schema name already exists in the database
        if get_tenant_model().objects.filter(schema_name=name).exists():
            raise forms.ValidationError(f"'{name}' mağaza adı zaten kullanılıyor. Lütfen başka bir ad seçin.")

        return name

    def save(self, commit=True):
        tenant = super().save(commit=False)
        tenant.schema_name = self.cleaned_data['name'].lower()
        if commit:
            # First, save the tenant in the public schema
            tenant.save()

            # Create a superuser for this new tenant
            connection.set_tenant(tenant)
            user = get_user_model().objects.create_user(
                username=self.cleaned_data['email'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password'],
                is_staff=True,
                is_superuser=True,
            )
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.save()

            # Switch back to the public schema
            connection.set_tenant(get_tenant_model().objects.get(schema_name='public'))
        return tenant