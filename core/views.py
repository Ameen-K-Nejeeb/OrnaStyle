from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from .decorators import admin_only_required, staff_or_vendor_required
from django.db.models import Q
from .forms import (
    AdminUserManagementForm,
    JewelryItemForm,
    OrderItemStatusForm,
    UserRegisterForm,
)
from .models import Category, JewelryItem, Order, OrderItem


from django.contrib.auth import get_user_model
from .decorators import admin_only_required


User = get_user_model()


# ==========================================
# PUBLIC STOREFRONT
# ==========================================
def home_view(request):
    items = JewelryItem.objects.filter(is_active=True).select_related('vendor', 'category').order_by('-created_at')
    categories = Category.objects.all()
    return render(request, 'store/home.html', {'items': items, 'categories': categories})


def product_detail_view(request, pk):
    item = get_object_or_404(JewelryItem, pk=pk, is_active=True)
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


@login_required
def direct_buy_view(request, pk):
    """Simulated instantaneous jewelry acquisition for demo checkout flow."""
    item = get_object_or_404(JewelryItem, pk=pk, is_active=True)
    if item.stock < 1:
        messages.error(request, "This jewel is currently out of stock.")
        return redirect('product_detail', pk=pk)

    order = Order.objects.create(
        customer=request.user,
        full_name=request.user.get_full_name() or request.user.username,
        shipping_address="Standard Atelier Delivery Address on File",
        contact_phone="+1 (555) 019-2834",
        total_amount=item.price
    )
    OrderItem.objects.create(
        order=order,
        item=item,
        vendor=item.vendor,
        price_at_purchase=item.price,
        quantity=1
    )
    item.stock -= 1
    item.save(update_fields=['stock'])
    messages.success(request, f"Acquisition registered! Order #{order.id} sent to master artisan.")
    return redirect('home')


# ==========================================
# CUSTOM ADMIN / VENDOR HYBRID PORTAL
# ==========================================
@staff_or_vendor_required
def dashboard_view(request):
    is_admin = request.user.is_custom_admin()

    if is_admin:
        items = JewelryItem.objects.all().select_related('vendor', 'category').order_by('-created_at')
        order_items = OrderItem.objects.all().select_related('order', 'item', 'vendor').order_by('-order__created_at')
        total_revenue = OrderItem.objects.exclude(status=OrderItem.Status.CANCELLED).aggregate(
            rev=Sum('price_at_purchase')
        )['rev'] or Decimal('0.00')
    else:
        # Vendor strict isolation
        items = JewelryItem.objects.filter(vendor=request.user).select_related('category').order_by('-created_at')
        order_items = OrderItem.objects.filter(vendor=request.user).select_related('order', 'item').order_by('-order__created_at')
        total_revenue = OrderItem.objects.filter(vendor=request.user).exclude(status=OrderItem.Status.CANCELLED).aggregate(
            rev=Sum('price_at_purchase')
        )['rev'] or Decimal('0.00')

    context = {
        'items': items,
        'order_items': order_items,
        'total_revenue': total_revenue,
        'is_admin': is_admin,
    }
    return render(request, 'custom_admin/dashboard.html', context)


@staff_or_vendor_required
def item_create_view(request):
    if request.method == 'POST':
        form = JewelryItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.vendor = request.user  # Automatically assigned to logged-in user
            item.save()
            messages.success(request, f'"{item.title}" successfully added.')
            return redirect('dashboard')
    else:
        form = JewelryItemForm()
    return render(request, 'custom_admin/form.html', {'form': form, 'title': 'Enlist New Piece'})


@staff_or_vendor_required
def item_update_view(request, pk):
    item = get_object_or_404(JewelryItem, pk=pk)
    # Isolation: vendors cannot edit other vendors' items
    if not request.user.is_custom_admin() and item.vendor != request.user:
        raise PermissionDenied("You can only modify your own creations.")

    if request.method == 'POST':
        form = JewelryItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{item.title}" updated.')
            return redirect('dashboard')
    else:
        form = JewelryItemForm(instance=item)
    return render(request, 'custom_admin/form.html', {'form': form, 'title': f'Refine: {item.title}'})


@staff_or_vendor_required
def item_toggle_status_view(request, pk):
    item = get_object_or_404(JewelryItem, pk=pk)
    if not request.user.is_custom_admin() and item.vendor != request.user:
        raise PermissionDenied("You can only change status for your own creations.")

    item.is_active = not item.is_active
    item.save(update_fields=['is_active'])
    status_label = 'Activated' if item.is_active else 'Deactivated (Hidden)'
    messages.info(request, f'"{item.title}" is now {status_label}.')
    return redirect('dashboard')


@staff_or_vendor_required
def item_delete_view(request, pk):
    item = get_object_or_404(JewelryItem, pk=pk)
    if not request.user.is_custom_admin() and item.vendor != request.user:
        raise PermissionDenied("You can only delete your own creations.")

    if request.method == 'POST':
        item.delete()
        messages.warning(request, f'"{item.title}" permanently deleted.')
        return redirect('dashboard')
    return render(request, 'custom_admin/confirm_delete.html', {'item': item})


@staff_or_vendor_required
def order_item_status_update_view(request, pk):
    """Allows vendors to update delivery state of their incoming items, or admins to update any."""
    order_item = get_object_or_404(OrderItem, pk=pk)
    if not request.user.is_custom_admin() and order_item.vendor != request.user:
        raise PermissionDenied("Access restricted to assigned artisan.")

    if request.method == 'POST':
        form = OrderItemStatusForm(request.POST, instance=order_item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Order #{order_item.order.id} status updated to {order_item.get_status_display()}.")
            return redirect('dashboard')
    else:
        form = OrderItemStatusForm(instance=order_item)

    return render(request, 'custom_admin/order_status_form.html', {'form': form, 'order_item': order_item})


# ==========================================
# ADMIN-ONLY GOVERNANCE
# ==========================================
@admin_only_required
def admin_manage_users_view(request):
    """Admin-only view to inspect, promote/demote, and toggle all platform accounts."""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'custom_admin/users_list.html', {'users': users})


@admin_only_required
def admin_user_edit_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = AdminUserManagementForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Account privileges for {target_user.username} saved.")
            return redirect('admin_users')
    else:
        form = AdminUserManagementForm(instance=target_user)
    return render(request, 'custom_admin/form.html', {'form': form, 'title': f'Manage Privileges: {target_user.username}'})


@admin_only_required
def admin_manage_users_view(request):
    """Admin directory with live stats, search querying, and role tab filtering."""
    search_query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', 'ALL').strip().upper()

    users_qs = User.objects.all().order_by('-date_joined')

    # Total counts before query-filtering
    total_users_count = users_qs.count()
    vendors_count = users_qs.filter(role=User.Role.VENDOR).count()
    customers_count = users_qs.filter(role=User.Role.CUSTOMER).count()
    admins_count = users_qs.filter(role=User.Role.ADMIN).count()
    suspended_count = users_qs.filter(is_active=False).count()

    # Search filter
    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Role tab filter
    if role_filter in [User.Role.ADMIN, User.Role.VENDOR, User.Role.CUSTOMER]:
        users_qs = users_qs.filter(role=role_filter)
    elif role_filter == 'SUSPENDED':
        users_qs = users_qs.filter(is_active=False)

    context = {
        'users': users_qs,
        'search_query': search_query,
        'role_filter': role_filter,
        'total_users_count': total_users_count,
        'vendors_count': vendors_count,
        'customers_count': customers_count,
        'admins_count': admins_count,
        'suspended_count': suspended_count,
    }
    return render(request, 'custom_admin/users_list.html', context)


@admin_only_required
def admin_user_toggle_status_view(request, pk):
    """Admin-only toggle to suspend or reactivate a user account."""
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, "You cannot suspend your own administrative account.")
        return redirect('admin_users')

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])
    state = "Active" if target_user.is_active else "Suspended"
    messages.info(request, f"Account '{target_user.username}' is now {state}.")
    return redirect('admin_users')



def about_view(request):
    return render(request, 'store/about.html')