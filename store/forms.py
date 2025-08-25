# store/forms.py

# Import the forms module from Django and our Address model.
from django import forms
from .models import Address, User, Review
from django.contrib.auth.forms import UserCreationForm

# We are creating a ModelForm. This special type of form is automatically
# generated from a Django Model. It's a very fast and professional way to handle data input.
class OrderCreateForm(forms.ModelForm):
    # The Meta class provides configuration for the ModelForm.
    class Meta:
        # Tell the ModelForm which model it should be built from.
        model = Address

        # 'exclude' is the opposite of 'fields'. It specifies which model fields
        # should NOT be included in the form. We exclude 'user' and 'is_default'
        # because we will handle them programmatically in the view.
        exclude = ['user', 'is_default']

        # Optional: Customize the human-readable labels that users will see for each field.
        # If we don't provide this, Django will use the model field names (e.g., 'full_name').
        labels = {
            'full_name': 'Full Name',
            'phone_number': 'Phone Number',
            'address_line_1': 'Address Line',
            'city': 'City',
            'postal_code': 'Postal Code',
        }

        # Optional: Add HTML attributes (like CSS classes) to the form field widgets.
        # This allows us to apply Bootstrap styling directly from our form definition.
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        # Tell the form to use our custom User model
        model = User
        # Specify the fields to display on the registration form
        fields = ('username', 'email', 'first_name', 'last_name')


class ReviewForm(forms.ModelForm):
    # We create a custom field for the rating using a ChoiceField with a Select widget.
    # This will render as a dropdown menu (1, 2, 3, 4, 5).
    rating = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Review
        # We only want the user to input the rating and their comment.
        # 'product' and 'user' will be set automatically in the view.
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'rating': 'Puanınız',
            'comment': 'Yorumunuz',
        }