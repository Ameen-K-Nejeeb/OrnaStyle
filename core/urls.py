from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Storefront & About
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('jewelry/<int:pk>/', views.product_detail_view, name='product_detail'),

    # Vault Cart Operations
    path('cart/', views.cart_detail_view, name='cart_detail'),
    path('cart/add/<int:pk>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/item/<int:pk>/update/', views.update_cart_item_view, name='update_cart_item'),

    # Account Hub & Address Studio
    path('account/', views.account_profile_view, name='account_profile'),
    path('account/address/new/', views.address_create_view, name='address_create'),
    path('account/address/<int:pk>/edit/', views.address_edit_view, name='address_edit'),
    path('account/address/<int:pk>/delete/', views.address_delete_view, name='address_delete'),

    # Razorpay Payment Gateway Endpoints
    path('payment/razorpay/order/', views.razorpay_create_order_view, name='razorpay_create_order'),
    path('payment/razorpay/callback/', views.razorpay_callback_view, name='razorpay_callback'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Shared Vendor/Admin Portal
    path('portal/dashboard/', views.dashboard_view, name='dashboard'),
    path('portal/items/new/', views.item_create_view, name='item_create'),
    path('portal/items/<int:pk>/edit/', views.item_update_view, name='item_update'),
    path('portal/items/<int:pk>/toggle/', views.item_toggle_status_view, name='item_toggle_status'),
    path('portal/items/<int:pk>/delete/', views.item_delete_view, name='item_delete'),
    path('portal/orders/<int:pk>/status/', views.order_item_status_update_view, name='order_status_update'),

    # Admin Exclusive User Governance
    path('portal/admin/users/', views.admin_manage_users_view, name='admin_users'),
    path('portal/admin/users/<int:pk>/edit/', views.admin_user_edit_view, name='admin_user_edit'),
    path('portal/admin/users/<int:pk>/toggle/', views.admin_user_toggle_status_view, name='admin_user_toggle'),
]