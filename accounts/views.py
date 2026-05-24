from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounts.models import EmailVerification, PasswordReset
from store.models import Order, TextToSpeechRequest 
from store.views import orders
from .utils import send_verification_code, send_password_reset_email
from django.contrib.auth import get_user_model
from django.conf import settings

from .forms import UserRegisterForm

User = get_user_model()

# Create your views here.
def custom_404_view(request, exception):
    return render(request, 'accounts/404.html', status=404)

def custom_500_view(request):
    return render(request, 'accounts/500.html', status=500)

@login_required(login_url='login')
def home(request):
    orders = Order.objects.filter(user=request.user)
    completed_orders_count = orders.filter(status='completed').count() if orders else 0
    tts_jobs_count = TextToSpeechRequest.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    
    context = {
        'orders': orders,
        'completed_orders_count': completed_orders_count,
        'tts_jobs_count': tts_jobs_count
    }
    
    return render(request, 'accounts/dashboard.html', context)

def register(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('home')
    form = UserRegisterForm()
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            
            user = authenticate(request, email=email, password=password)
            if user is not None:
                user.password_changed = True  # Mark password as changed
                user.save()
                auth_login(request, user)

            messages.success(request, 'Registration and login successful!')
            return redirect('home')
        else:
            errors = form.errors.as_json()
            messages.error(request, errors)
            return redirect('register')
        
    context = {'form': form}
    return render(request, 'accounts/register.html', context)

def login_view(request):
    print(settings.FLUTTERWAVE_SECRET_KEY)
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # check if the user with the provided email exists
        active_user = User.objects.filter(email=email).first()
        if active_user and active_user.password_changed == False:
            messages.error(request, 'Please change your password before logging in.')
            return redirect('reset_password')
        elif active_user and active_user.password_changed == True:
            user = authenticate(request, email=email, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, 'Login successful!')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')
        
    return render(request, 'accounts/login.html')

def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')



def send_verification(request):
    if request.user.email_verified:
        return JsonResponse({'message': 'Email is already verified.'}, status=400)
    """Utility function to send a verification email to the user."""
    verification = EmailVerification.generate_for_user(request.user)
    email_sent = send_verification_code(request.user, verification)
    
    if email_sent:
        return JsonResponse({'message': 'Verification email sent successfully.'}, status=200)
    
    else:
        return JsonResponse({'message': 'Failed to send verification email.'}, status=500)
   

def resend_verification(request):
    if request.user.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('home')
    """View to resend the verification email."""
    verification = EmailVerification.generate_for_user(request.user)
    email_sent = send_verification_code(request.user, verification)
    
    if email_sent:
        messages.success(request, 'Verification email resent successfully.')
    else:
        messages.error(request, 'Failed to resend verification email. Please try again later.')
    
    return redirect('verification_view')

def verification_view(request):
    if request.user.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('home')
    return render(request, 'accounts/verification.html')

def verify_email(request):
    """View to handle email verification using the provided token."""
    if request.method == "POST":
        token = request.POST.get('token')
        verification = get_object_or_404(EmailVerification, code=token)
        
        if verification.is_valid():
            verification.verified = True
            verification.save()
            
            user = verification.user
            user.email_verified = True
            user.save()
            
            messages.success(request, 'Email verified successfully!.')
            return redirect('home')
        else:
            messages.error(request, 'Invalid or expired verification code.')
            return redirect('verify_email')
    
    return render(request, 'accounts/verify_email.html')

@login_required(login_url='login')
def edit_email(request):
    if request.method == 'POST':
        new_email = request.POST.get('email')
        if new_email:
            request.user.email = new_email
            request.user.email_verified = False  # Mark email as unverified until re-verified
            request.user.save()
            
            messages.success(request, 'Email updated successfully.')
            return redirect('home')
        else:
            messages.error(request, 'Please provide a valid email address.')
            return redirect('edit_email')
        
    return render(request, 'accounts/edit_email.html')

@login_required(login_url='login')
def change_password(request):
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')
    if request.method == 'POST' and new_password and confirm_password:
        if new_password == confirm_password:
            request.user.set_password(new_password)
            request.user.password_changed = True  # Mark password as changed
            request.user.save()
            messages.success(request, 'Password changed successfully. Please log in again.')
            return redirect('login')
        else:
            messages.error(request, 'Passwords do not match.')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')


def confirm_password_reset(request, reset_token):
    password_reset = get_object_or_404(PasswordReset, token=reset_token)
    if not password_reset.is_valid():
        messages.error(request, 'This password reset link is invalid or has expired.')
        return redirect('reset_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password and confirm_password:
            if new_password == confirm_password:
                user = password_reset.user
                user.set_password(new_password)
                user.password_changed = True
                user.save()
                password_reset.used = True
                password_reset.save()
                messages.success(request, 'Your password has been reset successfully. Please log in.')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')

    return render(request, 'accounts/change_password.html')


def reset_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        
        if user:
            reset_entry = PasswordReset.generate_for_user(user)
            email_sent = send_password_reset_email(request, user, reset_entry)
            
            if email_sent:
                messages.success(request, 'Password reset instructions have been sent to your email.')
            else:
                messages.error(request, 'Failed to send password reset email. Please try again later.')
                
            return redirect('login')
        else:
            messages.error(request, 'No account found with that email address.')
            return redirect('reset_password')
    
    return render(request, 'accounts/reset_password.html')
