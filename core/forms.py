from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import JewelryItem

User = get_user_model()


class UserRegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (User.Role.CUSTOMER, 'Customer (Shopper)'),
            (User.Role.VENDOR, 'Artisan / Vendor (Seller)'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none bg-rose-50/30 text-stone-800'
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-2.5 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none bg-rose-50/30 text-stone-800'
                })


class JewelryItemForm(forms.ModelForm):
    class Meta:
        model = JewelryItem
        fields = [
            'title', 'category', 'material', 'price',
            'weight_in_grams', 'stock', 'description', 'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none'}),
            'material': forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none'}),
            'weight_in_grams': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'w-full px-4 py-2 rounded-xl border border-rose-200 focus:ring-2 focus:ring-amber-400 focus:outline-none bg-rose-50/20'}),
        }