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
    is_active = models.BooleanField(
        default=True,
        help_text='Soft delete flag: Uncheck to hide from public storefront.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Order(models.Model):
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders'
    )
    full_name = models.CharField(max_length=150)
    shipping_address = models.TextField()
    contact_phone = models.CharField(max_length=30)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"


class OrderItem(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Confirmation'
        PROCESSING = 'PROCESSING', 'In Atelier (Processing)'
        SHIPPED = 'SHIPPED', 'Dispatched / In Transit'
        DELIVERED = 'DELIVERED', 'Delivered & Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items'
    )
    item = models.ForeignKey(
        JewelryItem, on_delete=models.SET_NULL, null=True
    )
    vendor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='vendor_order_items'
    )
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.title if self.item else 'Archived Item'} (x{self.quantity})"