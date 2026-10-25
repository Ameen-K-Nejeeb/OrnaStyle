from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Category, JewelryItem


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'role',
        'is_staff',
        'is_superuser',
        'date_joined',
    )
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Role Permissions', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Permissions', {'fields': ('role',)}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(JewelryItem)
class JewelryItemAdmin(admin.ModelAdmin):
    list_display = (
        'image_thumbnail',
        'title',
        'category',
        'material',
        'price',
        'stock',
        'weight_in_grams',
        'vendor',
        'created_at',
    )
    list_filter = ('material', 'category', 'created_at', 'vendor')
    search_fields = ('title', 'description', 'vendor__username')
    list_editable = ('price', 'stock')
    autocomplete_fields = ('vendor', 'category')
    readonly_fields = ('created_at', 'image_preview')

    fieldsets = (
        ('Basic Details', {'fields': ('title', 'category', 'vendor', 'description')}),
        ('Material & Specs', {'fields': ('material', 'weight_in_grams', 'price', 'stock')}),
        ('Media', {'fields': ('image', 'image_preview')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

    @admin.display(description='Preview')
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 6px; border: 1px solid #D4AF37;" />',
                obj.image.url
            )
        return format_html('<span style="color: #999; font-size: 11px;">No Image</span>')

    @admin.display(description='Current Image')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; border-radius: 8px; border: 1px solid #ddd;" />',
                obj.image.url
            )
        return 'No image currently uploaded.'