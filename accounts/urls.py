from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('send-verification/', views.send_verification, name='send_verification'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('verification/', views.verification_view, name='verification_view'),
    path('edit-email/', views.edit_email, name='edit_email'),
    path('edit-password/', views.change_password, name='change_password'),
    path('password-reset/', views.reset_password, name='reset_password'),
    path('password-reset/<str:reset_token>/', views.confirm_password_reset, name='password_reset_confirm'),
    
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.admin_users, name='admin_users'),
    path('search-users/', views.search_users, name='search_users'),
    
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:email_id>/', views.email_detail, name='email_detail'),
    path('webhooks/resend/', views.resend_webhook, name='resend_webhook'),

    path('fund-wallet/', views.fund_account, name='fund_wallet'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    path('initialize-payment/<amount>/', views.initialize_payment, name='initialize_payment'),
]
