from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
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
]