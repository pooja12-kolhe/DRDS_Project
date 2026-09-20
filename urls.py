"""
URL configuration for ration_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from core import views


urlpatterns = [
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),

    path('shop-dashboard/', views.shop_dashboard, name='shop_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),  # ✅ FIXED

    path('distribute/', views.distribute_ration, name='distribute_ration'),
    path('user-allowance/<int:user_id>/', views.get_user_allowance, name='get_user_allowance'),

    path('history/', views.user_history, name='user_history'),

    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('transparency/', views.transparency, name='transparency'),
    path('update-stock/', views.update_stock, name='update_stock'),
    path('add-user/', views.add_user, name='add_user'),
    path('edit-user/<int:id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:id>/', views.delete_user, name='delete_user'),
    path('add-member/', views.add_member, name='add_member'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout, name='logout'),
    path('receipt/', views.receipt, name='receipt'),
    path('delete/<int:id>/', views.delete_record, name='delete_record'),

    path('admin/', admin.site.urls),
]