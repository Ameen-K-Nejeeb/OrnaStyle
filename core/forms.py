from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import JewelryItem, OrderItem

User = get_user_model()

INPUT_STYLE = (
    'w-full px-4 py-2.5 rounded-xl border border-ornagold-200/80 '
    'focus:ring-2 focus:ring-ornagold-400 focus:outline-none bg-rose-50/20 text-stone-800 text-sm'
)


class UserRegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (User.Role.CUSTOMER, 'Customer (Shopper & Collector)'),
            (User.Role.VENDOR, 'Artisan / Vendor (Jewelry Seller)'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': INPUT_STYLE}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = None
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': INPUT_STYLE})


class JewelryItemForm(forms.ModelForm):
    class Meta:
        model = JewelryItem
        fields = [
            'title', 'category', 'material', 'price',
            'weight_in_grams', 'stock', 'description', 'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'e.g. 18K Solitaire Ring'}),
            'category': forms.Select(attrs={'class': INPUT_STYLE}),
            'material': forms.Select(attrs={'class': INPUT_STYLE}),
            'price': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': '0.00', 'step': '0.01'}),
            'weight_in_grams': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': '0.00', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': INPUT_STYLE, 'placeholder': '1'}),
            'description': forms.Textarea(attrs={'class': INPUT_STYLE, 'rows': 4, 'placeholder': 'Artisan craft notes...'}),
            'image': forms.FileInput(attrs={'class': 'w-full text-xs text-stone-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-ornagold-100 file:text-ornagold-700 hover:file:bg-ornagold-200'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = None


class OrderItemStatusForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': INPUT_STYLE})
        }


class AdminUserManagementForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_STYLE}),
            'email': forms.EmailInput(attrs={'class': INPUT_STYLE}),
            'role': forms.Select(attrs={'class': INPUT_STYLE}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-ornagold-600 rounded focus:ring-ornagold-400'}),
        }