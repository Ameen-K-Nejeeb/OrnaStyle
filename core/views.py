from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from .decorators import staff_or_vendor_required
from .forms import JewelryItemForm, UserRegisterForm
from .models import Category, JewelryItem


def home_view(request):
    items = JewelryItem.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'store/home.html', {'items': items, 'categories': categories})


def product_detail_view(request, pk):
    item = get_object_or_404(JewelryItem, pk=pk)
    return render(request, 'store/detail.html', {'item': item})


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@staff_or_vendor_required
def dashboard_view(request):
    if request.user.is_custom_admin():
        items = JewelryItem.objects.all().select_related('vendor', 'category')
    else:
        items = JewelryItem.objects.filter(vendor=request.user).select_related('category')
    return render(request, 'custom_admin/dashboard.html', {'items': items})


@staff_or_vendor_required
def item_create_view(request):
    if request.method == 'POST':
        form = JewelryItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.vendor = request.user
            item.save()
            return redirect('dashboard')
    else:
        form = JewelryItemForm()
    return render(request, 'custom_admin/form.html', {'form': form, 'title': 'Add New Creation'})


@staff_or_vendor_required
def item_update_view(request, pk):
    item = get_object_or_404(JewelryItem, pk=pk)
    if not request.user.is_custom_admin() and item.vendor != request.user:
        raise PermissionDenied("You can only edit your own collection.")

    if request.method == 'POST':
        form = JewelryItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = JewelryItemForm(instance=item)
    return render(request, 'custom_admin/form.html', {'form': form, 'title': f'Refine: {item.title}'})


@staff_or_vendor_required
def item_delete_view(request, pk):
    item = get_object_or_404(JewelryItem, pk=pk)
    if not request.user.is_custom_admin() and item.vendor != request.user:
        raise PermissionDenied("You can only remove your own creations.")

    if request.method == 'POST':
        item.delete()
        return redirect('dashboard')
    return render(request, 'custom_admin/confirm_delete.html', {'item': item})