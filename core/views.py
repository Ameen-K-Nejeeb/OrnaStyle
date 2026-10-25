import razorpay
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .decorators import admin_only_required, staff_or_vendor_required
from .forms import (
    AddressForm,
    AdminUserManagementForm,
    JewelryItemForm,
    OrderItemStatusForm,
    UserProfileForm,
    UserRegisterForm,
)
from .models import Address, Cart, CartItem, Category, JewelryItem, Order, OrderItem

User = get_user_model()

# Razorpay Client Initialization
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


# ==========================================
# PUBLIC STOREFRONT & NARRATIVE
# ==========================================
def home_view(request):
    """Public Storefront: displays active jewelry creations ordered chronologically."""
    items = (
        JewelryItem.objects.filter(is_active=True)
        .select_related('vendor', 'category')
        .order_by('-created_at')
    )
    categories = Category.objects.all()
    return render(request, 'store/home.html', {'items': items, 'categories': categories})


def about_view(request):
    """Atelier heritage, ethical craftsmanship vows, and interactive 3D showcase."""
    return render(request, 'store/about.html')


def product_detail_view(request, pk):
    """Detailed specifications, precious metal hallmarks, and add-to-cart action."""
    item = get_object_or_404(JewelryItem, pk=pk, is_active=True)
    return render(request, 'store/detail.html', {'item': item})


def register_view(request):
    """Public onboarding for Shoppers (Customers) and Artisans (Vendors)."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to OrnaStyle Atelier, {user.username}.")
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


# ==========================================
# VAULT CASE (CART) OPERATIONS
# ==========================================
@login_required
def add_to_cart_view(request, pk):
    """Enrolls a selected jewelry item into the patron's authenticated Cart."""
    if request.user.is_custom_admin():
        messages.error(request, "Administrators cannot perform cart operations.")
        return redirect('dashboard')

    jewelry = get_object_or_404(JewelryItem, pk=pk, is_active=True)
    if jewelry.stock < 1:
        messages.error(request, "This jewel is presently out of vault stock.")
        return redirect('product_detail', pk=pk)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, jewelry=jewelry)

    if not created:
        if cart_item.quantity < jewelry.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Updated quantity for '{jewelry.title}'.")
        else:
            messages.warning(request, "Maximum vault allocation reached for this creation.")
    else:
        messages.success(request, f"'{jewelry.title}' placed into your Vault Case.")

    return redirect('cart_detail')


@login_required
def cart_detail_view(request):
    """Renders the cart contents, subtotal valuation, and shipping destination selector."""
    if request.user.is_custom_admin():
        messages.info(request, "Administrators do not maintain a client shopping cart.")
        return redirect('dashboard')

    cart, _ = Cart.objects.get_or_create(user=request.user)
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    selected_address = addresses.filter(is_default=True).first() or addresses.first()

    context = {
        'cart': cart,
        'addresses': addresses,
        'selected_address': selected_address,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'store/cart.html', context)


@login_required
def update_cart_item_view(request, pk):
    """Modifies line item quantities or purges an item from the Cart."""
    if request.user.is_custom_admin():
        return redirect('dashboard')

    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    action = request.POST.get('action')

    if action == 'increase':
        if cart_item.quantity < cart_item.jewelry.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.warning(request, "Stock ceiling reached for this item.")
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif action == 'remove':
        cart_item.delete()
        messages.info(request, "Piece removed from your Vault Case.")

    return redirect('cart_detail')


# ==========================================
# ACCOUNT PROFILE & ADDRESS STUDIO
# ==========================================
@login_required
def account_profile_view(request):
    """Personal sanctuary for customers; Admins manage settings through the dashboard."""
    if request.user.is_custom_admin():
        return redirect('dashboard')

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Account profile credentials successfully saved.")
            return redirect('account_profile')
    else:
        user_form = UserProfileForm(instance=request.user)

    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')

    context = {
        'user_form': user_form,
        'addresses': addresses,
        'orders': orders,
    }
    return render(request, 'store/account.html', context)


@login_required
def address_create_view(request):
    """Registers a new shipping destination (e.g. Peermade, Idukki, Kerala)."""
    if request.user.is_custom_admin():
        return redirect('dashboard')

    next_url = request.GET.get('next', 'account_profile')
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if not Address.objects.filter(user=request.user).exists():
                address.is_default = True
            address.save()
            messages.success(request, "New destination address saved.")
            return redirect(next_url)
    else:
        form = AddressForm()

    return render(request, 'store/address_form.html', {'form': form, 'title': 'Register New Address'})


@login_required
def address_edit_view(request, pk):
    """Edits an existing delivery address belonging to the user."""
    if request.user.is_custom_admin():
        return redirect('dashboard')

    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address details updated.")
            return redirect('account_profile')
    else:
        form = AddressForm(instance=address)

    return render(request, 'store/address_form.html', {'form': form, 'title': 'Refine Address Details'})


@login_required
def address_delete_view(request, pk):
    """Removes a stored delivery address."""
    if request.user.is_custom_admin():
        return redirect('dashboard')

    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.info(request, "Address destination removed.")
    return redirect('account_profile')


# ==========================================
# RAZORPAY PAYMENT GATEWAY
# ==========================================
@login_required
def razorpay_create_order_view(request):
    """Generates a Razorpay Order ID in INR Paise based on the cart total."""
    if request.method != 'POST' or request.user.is_custom_admin():
        return JsonResponse({'error': 'Invalid request method or permissions.'}, status=400)

    cart = Cart.objects.filter(user=request.user).first()
    if not cart or not cart.items.exists():
        return JsonResponse({'error': 'Your Vault Case is empty.'}, status=400)

    address_id = request.POST.get('address_id')
    address = Address.objects.filter(id=address_id, user=request.user).first()
    if not address:
        return JsonResponse({'error': 'Please select a valid delivery destination address.'}, status=400)

    amount_in_paise = int(cart.total_price * 100)

    razorpay_order = razorpay_client.order.create({
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': '1',
    })

    return JsonResponse({
        'order_id': razorpay_order['id'],
        'amount': amount_in_paise,
        'currency': 'INR',
        'key': settings.RAZORPAY_KEY_ID,
        'user_name': address.full_name,
        'user_email': request.user.email or 'patron@ornastyle.com',
        'user_phone': address.phone_number,
        'address_id': address.id,
    })


@csrf_exempt
@login_required
def razorpay_callback_view(request):
    """Cryptographically verifies Razorpay signature, creates orders, and empties cart."""
    if request.method != 'POST' or request.user.is_custom_admin():
        return redirect('cart_detail')

    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    address_id = request.POST.get('address_id')

    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature,
    }

    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        messages.error(request, "Payment security verification failed. Please try again.")
        return redirect('cart_detail')

    cart = Cart.objects.filter(user=request.user).first()
    address = Address.objects.filter(id=address_id, user=request.user).first()

    if not cart or not address:
        messages.error(request, "Unable to finalize order records.")
        return redirect('home')

    snapshot = (
        f"{address.full_name}\n"
        f"Phone: {address.phone_number}\n"
        f"{address.street_address}{', ' + address.landmark if address.landmark else ''}\n"
        f"{address.city_or_town}, {address.district}, {address.state} - {address.pincode}"
    )

    order = Order.objects.create(
        customer=request.user,
        shipping_address=address,
        address_snapshot=snapshot,
        total_amount=cart.total_price,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        is_paid=True
    )

    for item in cart.items.select_related('jewelry', 'jewelry__vendor'):
        OrderItem.objects.create(
            order=order,
            item=item.jewelry,
            vendor=item.jewelry.vendor,
            price_at_purchase=item.jewelry.price,
            quantity=item.quantity,
            status=OrderItem.Status.PENDING
        )
        item.jewelry.stock = max(0, item.jewelry.stock - item.quantity)
        item.jewelry.save(update_fields=['stock'])

    cart.items.all().delete()
    messages.success(request, f"Payment Confirmed! Your order #{order.id} is being tailored in the atelier.")
    return redirect('account_profile')


# ==========================================
# CUSTOM ADMIN & VENDOR HYBRID PORTAL
# ==========================================
@staff_or_vendor_required
def dashboard_view(request):
    """Shared dashboard: Admins see platform-wide catalog/orders; vendors see only their creations."""
    is_admin = request.user.is_custom_admin()

    if is_admin:
        items = JewelryItem.objects.all().select_related('vendor', 'category').order_by('-created_at')
        order_items = OrderItem.objects.all().select_related('order', 'item', 'vendor').order_by('-order__created_at')
        total_revenue = OrderItem.objects.exclude(status=OrderItem.Status.CANCELLED).aggregate(
            rev=Sum('price_at_purchase')
        )['rev'] or Decimal('0.00')
    else:
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
    """Enlists a new creation. Admins choose the assigned vendor; vendors are auto-assigned."""
    is_admin = request.user.is_custom_admin()

    if request.method == 'POST':
        form = JewelryItemForm(request.POST, request.FILES, current_user=request.user)
        if form.is_valid():
            item = form.save(commit=False)
            if is_admin:
                selected_vendor = form.cleaned_data.get('vendor')
                item.vendor = selected_vendor if selected_vendor else request.user
            else:
                item.vendor = request.user

            item.save()
            messages.success(request, f'"{item.title}" successfully enrolled under artisan {item.vendor.username}.')
            return redirect('dashboard')
    else:
        form = JewelryItemForm(current_user=request.user)

    return render(request, 'custom_admin/form.html', {'form': form, 'title': 'Enlist New Piece'})


@staff_or_vendor_required
def item_update_view(request, pk):
    """Refines an item. Regular artisans are restricted from modifying other vendors' pieces."""
    item = get_object_or_404(JewelryItem, pk=pk)

    if not request.user.is_custom_admin() and item.vendor != request.user:
        raise PermissionDenied("You can only modify your own creations.")

    if request.method == 'POST':
        form = JewelryItemForm(request.POST, request.FILES, instance=item, current_user=request.user)
        if form.is_valid():
            updated_item = form.save(commit=False)
            if request.user.is_custom_admin():
                selected_vendor = form.cleaned_data.get('vendor')
                if selected_vendor:
                    updated_item.vendor = selected_vendor
            updated_item.save()
            messages.success(request, f'"{updated_item.title}" details updated.')
            return redirect('dashboard')
    else:
        form = JewelryItemForm(instance=item, current_user=request.user)

    return render(request, 'custom_admin/form.html', {'form': form, 'title': f'Refine: {item.title}'})


@staff_or_vendor_required
def item_toggle_status_view(request, pk):
    """Soft-delete toggle: hides or reveals pieces on the public storefront."""
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
    """Permanently purges a creation from the database."""
    item = get_object_or_404(JewelryItem, pk=pk)
    if not request.user.is_custom_admin() and item.vendor != request.user:
        raise PermissionDenied("You can only delete your own creations.")

    if request.method == 'POST':
        item.delete()
        messages.warning(request, f'"{item.title}" permanently purged.')
        return redirect('dashboard')
    return render(request, 'custom_admin/confirm_delete.html', {'item': item})


@staff_or_vendor_required
def order_item_status_update_view(request, pk):
    """Allows vendors to progress delivery states for their own order line items."""
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
# ADMIN-ONLY USER & VENDOR GOVERNANCE
# ==========================================
@admin_only_required
def admin_manage_users_view(request):
    """Admin directory with role categorization tabs, search query, and global stats."""
    search_query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', 'ALL').strip().upper()

    base_users = User.objects.all().order_by('-date_joined')

    total_users_count = base_users.count()
    vendors_count = base_users.filter(role=User.Role.VENDOR).count()
    customers_count = base_users.filter(role=User.Role.CUSTOMER).count()
    admins_count = base_users.filter(role=User.Role.ADMIN).count()

    users_qs = base_users
    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )

    if role_filter in [User.Role.ADMIN, User.Role.VENDOR, User.Role.CUSTOMER]:
        users_qs = users_qs.filter(role=role_filter)

    context = {
        'users': users_qs,
        'search_query': search_query,
        'role_filter': role_filter,
        'total_users_count': total_users_count,
        'vendors_count': vendors_count,
        'customers_count': customers_count,
        'admins_count': admins_count,
    }
    return render(request, 'custom_admin/users_list.html', context)


@admin_only_required
def admin_user_edit_view(request, pk):
    """Admin control to edit credentials or promote/demote user roles."""
    target_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = AdminUserManagementForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Permissions saved for {target_user.username}.")
            return redirect('admin_users')
    else:
        form = AdminUserManagementForm(instance=target_user)
    return render(request, 'custom_admin/form.html', {'form': form, 'title': f'Manage Privileges: {target_user.username}'})


@admin_only_required
def admin_user_toggle_status_view(request, pk):
    """Admin-only toggle to suspend or reactivate accounts, protected against self-suspension."""
    target_user = get_object_or_404(User, pk=pk)

    if target_user == request.user:
        messages.error(request, "Action blocked: You cannot suspend your own administrative account.")
        return redirect('admin_users')

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])

    state_label = 'Reactivated' if target_user.is_active else 'Suspended'
    messages.info(request, f"Account '{target_user.username}' has been successfully {state_label.lower()}.")
    return redirect('admin_users')