from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Storefront
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('jewelry/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('jewelry/<int:pk>/buy-now/', views.direct_buy_view, name='buy_now'),

    # Authentication
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