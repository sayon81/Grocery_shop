from django import forms
from .models import Order, UserProfile

class GroceryOrderForm(forms.ModelForm):
    """Form for single item order (used in order_items.html)"""
    
    quantity = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'quantity-input',
            'id': 'quantityInput',
            'min': '1',
            'max': '20'
        })
    )
    
    class Meta:
        model = Order
        fields = ['customer_name', 'phone_number', 'email', 'address', 'special_instructions']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your full name',
                'id': 'customer_name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your phone number',
                'id': 'phone_number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your email',
                'id': 'email'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your delivery address',
                'rows': 3,
                'id': 'address'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Any special instructions?',
                'rows': 2,
                'id': 'special_instructions'
            }),
        }


class CheckoutForm(forms.Form):
    """Form for checkout_cart.html (multiple items)"""
    
    customer_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your full name',
            'id': 'customer_name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
            'id': 'email'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your phone number',
            'id': 'phone_number'
        })
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your complete delivery address',
            'rows': 3,
            'id': 'address'
        }),
        required=True
    )
    
    special_instructions = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Any special instructions? (e.g., gate code, delivery time, etc.)',
            'rows': 2,
            'id': 'special_instructions'
        }),
        required=False
    )


class ContactForm(forms.Form):
    """Form for contact.html"""
    
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your Name',
            'id': 'contactName'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your Email',
            'id': 'contactEmail'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your Phone Number',
            'id': 'contactPhone'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Subject',
            'id': 'contactSubject'
        })
    )
    
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Your Message',
            'rows': 6,
            'id': 'contactMessage'
        })
    )


class UserProfileForm(forms.ModelForm):
    """Form for dashboard.html profile editing"""
    
    class Meta:
        model = UserProfile
        fields = ['contact_number', 'profile_pic']
        widgets = {
            'contact_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your phone number',
                'id': 'id_contact_number'
            }),
            'profile_pic': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
                'id': 'profile_pic'
            }),
        }


class AddressForm(forms.Form):
    """Form for dashboard.html address editing"""
    
    address = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your full address',
            'id': 'id_address'
        })
    )


class LoginForm(forms.Form):
    """Form for login.html"""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
            'id': 'email'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'id': 'password'
        })
    )
    
    remember = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'id': 'remember'
        })
    )


class SignupForm(forms.Form):
    """Form for signup.html"""
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your full name',
            'id': 'name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your email',
            'id': 'email'
        })
    )
    
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a password',
            'id': 'password'
        })
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
            'id': 'confirmPassword'
        })
    )
    
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'id': 'terms'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data


class SearchForm(forms.Form):
    """Form for search in navbar and item_search.html"""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'search-input',
            'placeholder': 'Search for groceries...',
            'id': 'searchInput'
        })
    )