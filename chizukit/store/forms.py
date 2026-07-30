from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Review

class OrderForm(forms.Form):
    email = forms.EmailField(label='Email address', required=True)
    first_name = forms.CharField(label='First Name', max_length=100, required=True)
    last_name = forms.CharField(label='Last Name', max_length=100, required=True)
    telephone = forms.CharField(label='Telephone', max_length=15, required=True)
    address_search = forms.CharField(label='Address search', max_length=255, required=False)
    street_address = forms.CharField(label='Street Address', max_length=255, required=True)
    country = forms.CharField(label='Country', max_length=100, required=True)
    state = forms.CharField(label='State/Province', max_length=100, required=True)
    postal_code = forms.CharField(label='Zip/Postal Code', max_length=20, required=True)
    city = forms.CharField(label='City', max_length=100, required=True)

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Email / Username')
    password = forms.CharField(widget=forms.PasswordInput)

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['comment', 'rating']
        widgets = {
            'rating': forms.RadioSelect()
        }