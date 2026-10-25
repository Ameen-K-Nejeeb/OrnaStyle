from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Store Administrator'
        VENDOR = 'VENDOR', 'Artisan / Vendor'
        CUSTOMER = 'CUSTOMER', 'Customer'

    role = models.CharField(
        max_length=15, choices=Role.choices, default=Role.CUSTOMER
    )

    def is_vendor(self):
        return self.role == self.Role.VENDOR

    def is_custom_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class JewelryItem(models.Model):
    MATERIAL_CHOICES = [
        ('18K_ROSE_GOLD', '18K Rose Gold'),
        ('24K_YELLOW_GOLD', '24K Yellow Gold'),
        ('WHITE_GOLD', 'White Gold'),
        ('DIAMOND_SOLITAIRE', 'Diamond & Solitaire'),
        ('PEARL_GEMSTONE', 'Freshwater Pearl & Gemstone'),
        ('STERLING_SILVER', '925 Sterling Silver'),
    ]

    vendor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='jewelry_items'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name='products'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    material = models.CharField(
        max_length=30, choices=MATERIAL_CHOICES, default='18K_ROSE_GOLD'
    )
    weight_in_grams = models.DecimalField(
        max_digits=6, decimal_places=2, help_text='Weight in grams'
    )
    stock = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='jewelry_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title