from decimal import Decimal
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
    phone = models.CharField(max_length=20, blank=True, null=True)

    def is_vendor(self):
        return self.role == self.Role.VENDOR

    def is_custom_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser


class Address(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='addresses'
    )
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255)
    landmark = models.CharField(max_length=150, blank=True, null=True)
    city_or_town = models.CharField(max_length=100)
    district = models.CharField(max_length=100, default='Idukki')
    state = models.CharField(max_length=100, default='Kerala')
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default address exists per user
            Address.objects.filter(user=self.user, is_default=True).exclude(
                id=self.id
            ).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.street_address}, {self.city_or_town}, {self.district} ({self.pincode})"


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
    weight_in_grams = models.DecimalField(max_digits=6, decimal_places=2)
    stock = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='jewelry_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Cart(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items'
    )
    jewelry = models.ForeignKey(JewelryItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.jewelry.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.jewelry.title}"


class Order(models.Model):
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='orders'
    )
    shipping_address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, null=True
    )
    address_snapshot = models.TextField(
        help_text="Immutable snapshot of the address at time of purchase"
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username} (${self.total_amount})"


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
    item = models.ForeignKey(JewelryItem, on_delete=models.SET_NULL, null=True)
    vendor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='vendor_order_items'
    )
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    updated_at = models.DateTimeField(auto_now=True)