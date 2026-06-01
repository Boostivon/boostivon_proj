from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from accounts.models import EmailVerification, PasswordReset
import resend
from store.models import Order, Platform, SocialMediaAccount, TextToSpeechRequest, Service, Transaction
from store.views import orders
from .utils import send_verification_code, send_password_reset_email
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Count, Q, Sum
from decimal import Decimal
import json
from django.views.decorators.csrf import csrf_exempt
from .models import ReceivedEmail
import requests

from .forms import UserRegisterForm

User = get_user_model()
RESEND_API_KEY = settings.RESEND_API_KEY

# Create your views here.
def custom_404_view(request, exception):
    return render(request, 'accounts/404.html', status=404)

def custom_500_view(request):
    return render(request, 'accounts/500.html', status=500)

def landing(request):
    return render(request, 'landing.html')

@login_required(login_url='login')
def home(request):
    # Show landing page to unauthenticated users
    if not request.user.is_authenticated:
        return render(request, 'landing.html')
    
    # Show dashboard to authenticated users
    orders = Order.objects.filter(user=request.user)
    completed_orders_count = orders.filter(status='completed').count() if orders else 0
    tts_jobs_count = TextToSpeechRequest.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    
    products = Platform.objects.filter(quantity__gt=0).order_by('-created_at')[:10] # Get the first 10 products for display
    
    context = {
        'orders': orders,
        'completed_orders_count': completed_orders_count,
        'tts_jobs_count': tts_jobs_count,
        'products': products,
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
            errors = next(iter(form.errors.values()))[0]
            print(errors)  # Log errors for debugging
            messages.error(request, errors)
            return redirect('register')
        
    context = {'form': form}
    return render(request, 'accounts/register.html', context)

def login_view(request):
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


# ============================ Admin views ============================
@login_required(login_url='login')
def admin_dashboard(request):
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('home')

    users = User.objects.all()
    user_count = users.count()
    customer_count = users.filter(role='customer').count()
    admin_count = users.filter(role='admin').count()

    orders = Order.objects.all()
    order_count = orders.count()
    completed_orders_count = orders.filter(status='completed').count()
    pending_orders_count = orders.filter(status='pending').count()
    cancelled_orders_count = orders.filter(status='cancelled').count()
    total_revenue = orders.filter(status='completed').aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    average_order_value = total_revenue / completed_orders_count if completed_orders_count else Decimal('0')

    platforms = Platform.objects.all()
    platform_count = platforms.count()
    total_accounts = SocialMediaAccount.objects.count()
    active_services_count = Service.objects.filter(is_active=True).count()
    tts_count = TextToSpeechRequest.objects.count()
    pending_tts_count = TextToSpeechRequest.objects.filter(status='pending').count()
    transaction_count = Transaction.objects.count()
    total_deposits = Transaction.objects.filter(transaction_type='deposit', status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_withdrawals = Transaction.objects.filter(transaction_type='withdrawal', status='completed').aggregate(total=Sum('amount'))['total'] or Decimal('0')

    top_services = Service.objects.annotate(order_count=Count('order')).order_by('-order_count')[:5]
    top_platforms = platforms.annotate(account_count=Count('socialmediaaccount')).order_by('-account_count')[:5]
    latest_orders = orders.order_by('-created_at')[:6]
    newest_users = users.order_by('-created_at')[:5]

    context = {
        'user_count': user_count,
        'customer_count': customer_count,
        'admin_count': admin_count,
        'order_count': order_count,
        'completed_orders_count': completed_orders_count,
        'pending_orders_count': pending_orders_count,
        'cancelled_orders_count': cancelled_orders_count,
        'total_revenue': f"{total_revenue:,.2f}",
        'average_order_value': f"{average_order_value:,.2f}" if average_order_value else '0.00',
        'platform_count': platform_count,
        'total_accounts': total_accounts,
        'active_services_count': active_services_count,
        'tts_count': tts_count,
        'pending_tts_count': pending_tts_count,
        'transaction_count': transaction_count,
        'total_deposits': f"{total_deposits:,.2f}",
        'total_withdrawals': f"{total_withdrawals:,.2f}",
        'top_services': top_services,
        'top_platforms': top_platforms,
        'latest_orders': latest_orders,
        'newest_users': newest_users,
    }

    return render(request, 'accounts/admin.html', context)

@login_required(login_url='login')
def admin_users(request):
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    users = User.objects.annotate(
        total_orders=Count('orders')
    ).order_by('-created_at')

    
    user_count = users.count()
    
    context = {
        'users': users,
        'user_count': user_count,
    }
    
    return render(request, 'accounts/admin-users.html', context)

@login_required(login_url='login')
def search_users(request):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    query = request.GET.get('q', '')
    users = User.objects.filter(username__icontains=query) | User.objects.filter(email__icontains=query)

    user_data = [
        {
            'username': user.username,
            'email': user.email,
            'wallet_balance': str(user.wallet_balance),
            'role': user.role,
            'total_orders': Order.objects.filter(user=user).count(),
        }
        for user in users
    ]

    return JsonResponse({'users': user_data})

@login_required(login_url='login')
def profile(request):
    user = request.user
    user_orders = user.orders.order_by('-created_at')[:6]
    completed_orders_count = user.orders.filter(status='completed').count()
    pending_orders_count = user.orders.filter(status='pending').count()
    cancelled_orders_count = user.orders.filter(status='cancelled').count()
    total_spent = user.orders.filter(status='completed').aggregate(total=Sum('total_price'))['total'] or Decimal('0')
    tts_jobs_count = TextToSpeechRequest.objects.filter(user=user).count()
    recent_tts = TextToSpeechRequest.objects.filter(user=user).order_by('-created_at')[:5]

    context = {
        'user': user,
        'user_orders': user_orders,
        'completed_orders_count': completed_orders_count,
        'pending_orders_count': pending_orders_count,
        'cancelled_orders_count': cancelled_orders_count,
        'total_spent': f"{total_spent:,.2f}",
        'tts_jobs_count': tts_jobs_count,
        'recent_tts': recent_tts,
    }
    return render(request, 'accounts/profile.html', context)

@login_required(login_url='login')
def edit_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        
        if username:
            request.user.username = username
        if email and email != request.user.email:
            request.user.email = email
            request.user.email_verified = False  # Mark email as unverified until re-verified
        
        request.user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    return render(request, 'accounts/edit_profile.html', {'user': request.user})


@csrf_exempt
def resend_webhook(request):
    if request.method != "POST":
        return JsonResponse({'error': 'Invalid request'}, status=405)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if payload.get('type') != 'email.received':
        return JsonResponse({'error': 'Unhandled event type'}, status=400)

    event_data = payload.get('data', {})
    email_id = event_data.get('email_id')

    # Fetch full email content from Resend API (webhook payload lacks text/html)
    full_email = event_data
    if email_id:
        try:
            response = requests.get(
                f"https://api.resend.com/emails/{email_id}",
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                timeout=10,
            )
            if response.ok:
                full_email = response.json()
        except requests.RequestException:
            pass  # Fall back to event_data if fetch fails
    
    email = resend.Emails.Receiving.get(email_id) if email_id else None
    sender      = full_email.get('from', '')
    subject     = full_email.get('subject', '') or '(No subject)'
    body        = email['html'] or email['text'] or ''
    message_id  = full_email.get('message_id', '')
    to_addresses  = full_email.get('to', []) or []
    cc_addresses  = full_email.get('cc', []) or []
    bcc_addresses = full_email.get('bcc', []) or []
    attachments   = full_email.get('attachments', []) or []

    created_at  = full_email.get('created_at') or payload.get('created_at')
    received_at = parse_datetime(created_at) if created_at else timezone.now()
    if timezone.is_naive(received_at):
        received_at = timezone.make_aware(received_at, timezone=timezone.utc)

    defaults = {
        'sender':      sender,
        'message_id':  message_id,
        'subject':     subject,
        'body':        body,
        'recipients':  to_addresses,
        'cc':          cc_addresses,
        'bcc':         bcc_addresses,
        'attachments': attachments,
        'received_at': received_at,
    }

    if email_id:
        ReceivedEmail.objects.update_or_create(email_id=email_id, defaults=defaults)
    elif message_id:
        ReceivedEmail.objects.update_or_create(message_id=message_id, defaults=defaults)
    else:
        ReceivedEmail.objects.create(**defaults)

    return JsonResponse({'success': True})

@login_required(login_url='login')
def inbox(request):
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    emails = ReceivedEmail.objects.all().order_by('-received_at')

    return render(request, 'accounts/inbox.html', {
        'emails': emails
    })
    
@login_required(login_url='login')
def email_detail(request, email_id):
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    email = get_object_or_404(ReceivedEmail, id=email_id)

    return render(request, 'accounts/email_detail.html', {
        'email': email
    })
    
@login_required(login_url='login')
def fund_account(request):
    if request.method == 'POST':
        
        amount = float(request.POST.get('amount'))
        
        if amount:
            if amount >= 1000:
                return redirect('initialize_payment', str(amount))
            else:
                messages.error(request, "Amount must not be less than ₦1000")
                return redirect('fund_wallet')
        else:
            messages.error(request, "Enter an amount")
            return redirect('fund_wallet')
    
    return render(request, 'accounts/fund_account.html')

def initialize_payment(request, amount):
    secret_key = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', None)
    if not secret_key:
        messages.error(request, "Payment gateway is not configured.")
        return redirect('fund_account')
    headers = {
        'Authorization': f'Bearer {secret_key}',
        'Content-Type': 'application/json',
    }
    data = {
        'tx_ref': f'{request.user.id}_{int(timezone.now().timestamp())}',
        'amount': f'{float(amount)}',
        'currency': 'NGN',
        'redirect_url': request.build_absolute_uri('/payment-callback/'),
        'customer': {
            'email': request.user.email,
            'name': request.user.username,
        },
        'customizations': {
            'title': f'Account Funding - {request.user.username}',
            'description': 'BOOSTIVON',
        },
    }
    try:
        response = requests.post('https://api.flutterwave.com/v3/payments', headers=headers, json=data, timeout=10)
        response_data = response.json()
        if response.ok and response_data.get('status') == 'success':
            payment_link = response_data['data']['link']
            return redirect(payment_link)
        else:
            messages.error(request, "Failed to initialize payment. Please try again.")
            return redirect('fund_wallet')
    except requests.RequestException:
        messages.error(request, "An error occurred while connecting to the payment gateway. Please try again.")
        return redirect('fund_wallet')
    
def payment_callback(request):
    status = request.GET.get('status')
    tx_ref = request.GET.get('tx_ref')
    transaction_id = request.GET.get('transaction_id')

    if status in ['successful', 'completed'] and tx_ref and transaction_id:
        secret_key = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', None)
        if not secret_key:
            messages.error(request, "Payment gateway is not configured.")
            return redirect('home')
        headers = {
            'Authorization': f'Bearer {secret_key}',
        }
        try:
            response = requests.get(f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify', headers=headers, timeout=10)
            response_data = response.json()
            if response.ok and response_data.get('status') == 'success':
                amount = float(response_data['data']['amount'])
                request.user.wallet_balance += Decimal(amount)
                request.user.save()
                Transaction.objects.create(
                    user=request.user,
                    amount=Decimal(amount),
                    transaction_type='deposit',
                    status='completed',
                    reference=tx_ref,
                    transaction_id=transaction_id,
                )
                messages.success(request, "Your account has been funded successfully!")
                return redirect('home')
            else:
                messages.error(request, "Payment verification failed. Please contact support.")
                return redirect('home')
        except requests.RequestException:
            messages.error(request, "An error occurred while verifying the payment. Please contact support.")
            return redirect('home')
    else:
        messages.error(request, "Payment was not successful. Please try again.")
        return redirect('home')
    
    
        
