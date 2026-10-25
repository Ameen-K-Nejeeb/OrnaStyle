from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('jewelry/<int:pk>/', views.product_detail_view, name='product_detail'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('portal/dashboard/', views.dashboard_view, name='dashboard'),
    path('portal/items/new/', views.item_create_view, name='item_create'),
    path('portal/items/<int:pk>/edit/', views.item_update_view, name='item_update'),
    path('portal/items/<int:pk>/delete/', views.item_delete_view, name='item_delete'),
]