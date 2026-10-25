from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Address, Category, JewelryItem, OrderItem

User = get_user_model()

INPUT_STYLE = (
    'w-full px-4 py-2.5 rounded-xl border border-ornagold-200/80 '
    'focus:ring-2 focus:ring-ornagold-400 focus:outline-none bg-rose-50/20 text-stone-800 text-sm'
)


class UserRegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (User.Role.CUSTOMER, 'Customer (Shopper & Collector)'),
            (User.Role.VENDOR, 'Vendor (Artisan & Seller)'),
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

        self.fields['username'].widget.attrs.update(
            {'placeholder': 'Enter your username'}
        )
        self.fields['email'].widget.attrs.update(
            {'placeholder': 'Enter your email'}
        )
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.update(
                {'placeholder': 'Enter password'}
            )
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update(
                {'placeholder': 'Confirm password'}
            )


class JewelryItemForm(forms.ModelForm):
    class Meta:
        model = JewelryItem
        fields = [
            'title',
            'category',
            'material',
            'price',
            'weight_in_grams',
            'stock',
            'description',
            'image',
        ]
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': INPUT_STYLE,
                    'placeholder': 'e.g. Royal Diamond Solitaire Ring',
                }
            ),
            'category': forms.Select(attrs={'class': INPUT_STYLE}),
            'material': forms.Select(attrs={'class': INPUT_STYLE}),
            'price': forms.NumberInput(
                attrs={
                    'class': INPUT_STYLE,
                    'placeholder': '0.00',
                    'step': '0.01',
                }
            ),
            'weight_in_grams': forms.NumberInput(
                attrs={
                    'class': INPUT_STYLE,
                    'placeholder': '0.00',
                    'step': '0.01',
                }
            ),
            'stock': forms.NumberInput(
                attrs={'class': INPUT_STYLE, 'placeholder': '1'}
            ),
            'description': forms.Textarea(
                attrs={
                    'class': INPUT_STYLE,
                    'rows': 4,
                    'placeholder': 'Artisan craft notes...',
                }
            ),
            'image': forms.FileInput(
                attrs={
                    'class': 'w-full text-xs text-stone-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-ornagold-100 file:text-ornagold-700 hover:file:bg-ornagold-200 cursor-pointer'
                }
            ),
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = current_user

        # If logged-in user is an Admin, include the vendor dropdown
        if self.current_user and self.current_user.is_custom_admin():
            self.fields['vendor'] = forms.ModelChoiceField(
                queryset=User.objects.filter(
                    role=User.Role.VENDOR, is_active=True
                ).order_by('username'),
                required=True,
                empty_label='Select Assigned Vendor / Artisan',
                widget=forms.Select(attrs={'class': INPUT_STYLE}),
                label='Assigned Artisan / Vendor',
            )
            # Reorder fields to display the vendor selector right after category
            ordered_fields = [
                'title',
                'category',
                'vendor',
                'material',
                'price',
                'weight_in_grams',
                'stock',
                'description',
                'image',
            ]
            self.order_fields(ordered_fields)

        for field in self.fields.values():
            field.help_text = None


class OrderItemStatusForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['status']
        widgets = {'status': forms.Select(attrs={'class': INPUT_STYLE})}


class AdminUserManagementForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': INPUT_STYLE}),
            'email': forms.EmailInput(attrs={'class': INPUT_STYLE}),
            'role': forms.Select(attrs={'class': INPUT_STYLE}),
            'is_active': forms.CheckboxInput(
                attrs={
                    'class': 'h-4 w-4 text-ornagold-600 rounded focus:ring-ornagold-400'
                }
            ),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': INPUT_STYLE, 'placeholder': 'name@example.com'}),
            'phone': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': '+91 98765 43210'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'full_name', 'phone_number', 'street_address', 'landmark',
            'city_or_town', 'district', 'state', 'pincode', 'is_default'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Recipient Full Name'}),
            'phone_number': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Contact Phone Number'}),
            'street_address': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'House Name, Street, locality'}),
            'landmark': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'Nearby Landmark (Optional)'}),
            'city_or_town': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'e.g. Peermade, Vandiperiyar, Kochi'}),
            'district': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'e.g. Idukki, Ernakulam'}),
            'state': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'e.g. Kerala'}),
            'pincode': forms.TextInput(attrs={'class': INPUT_STYLE, 'placeholder': 'e.g. 685531'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-ornagold-600 rounded focus:ring-ornagold-400'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = None