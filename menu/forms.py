from django import forms
from .models import Customer

class CheckoutForm(forms.ModelForm):
    inside_dhaka = forms.ChoiceField(
        choices=(
            ('yes', 'Inside Dhaka'),
            ('no', 'Outside Dhaka')
        ), 
        widget=forms.RadioSelect,
        label="Delivery Location"
    )
    
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address', 'city']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-amber-500 focus:ring-2 focus:ring-amber-200 transition-all duration-300',
                'placeholder': 'Enter your full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-amber-500 focus:ring-2 focus:ring-amber-200 transition-all duration-300',
                'placeholder': 'e.g., 01XXXXXXXXX'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-input w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-amber-500 focus:ring-2 focus:ring-amber-200 transition-all duration-300',
                'placeholder': 'Enter your complete delivery address',
                'rows': 3
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-amber-500 focus:ring-2 focus:ring-amber-200 transition-all duration-300',
                'placeholder': 'Enter your city',
                'value': 'Dhaka'
            }),
        }
        labels = {
            'name': 'Full Name',
            'phone': 'Phone Number', 
            'address': 'Delivery Address',
            'city': 'City'
        }
        help_texts = {
            'phone': 'We will contact you on this number for delivery updates',
            'address': 'Please provide detailed address including area, road, and house number',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove default colon from labels
        self.label_suffix = ""