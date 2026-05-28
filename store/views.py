import json
import uuid
from decimal import Decimal

import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import CreateOrderForm, PlatformForm, SocialMediaAccountForm
from .models import Platform, Service, Order, SocialMediaAccount, AccountOrder, UserPlatformAccount
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .providers.the_owlet import TheOwletAPI
from django.contrib.auth.decorators import login_required

# Create your views here.
def service_list(request):
    return render(request, "store/service_list.html")

@login_required(login_url='login')
def create_order(request):
    if request.user.email_verified == False:
        messages.error(request, 'Please verify your email before placing an order.')
        return redirect('verification_view')
    if request.method == 'POST':
        form = CreateOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_price = (order.service.price_per_k or Decimal('0.00')) * order.quantity / Decimal('1000')
            order.user = request.user  # Set the user based on the logged-in user
            order.status = 'pending'
            order.save()
            return redirect('store:initialize_payment', order.id)
        else:
            error = next(iter(form.errors.values()))[0]
            messages.error(request, error)
            return redirect('store:create_order')
    else:
        form = CreateOrderForm()
    return render(request, "store/order-new.html", {"form": form})

@login_required(login_url='login')
def initialize_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    secret_key = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', None)
    if not secret_key:
        return render(request, 'store/payment_status.html', {
            'order': order,
            'title': 'Payment Configuration Error',
            'message': 'Flutterwave secret key is missing. Please configure FLUTTERWAVE_SECRET_KEY.',
            'success': False,
        })

    tx_ref = f"boostivon-order-{order.id}-{uuid.uuid4().hex[:8]}"
    callback_url = request.build_absolute_uri(reverse('store:payment_callback', args=[order.id]))

    payload = {
        'tx_ref': tx_ref,
        'amount': str(order.total_price),
        'currency': 'NGN',
        'redirect_url': callback_url,
        'customer': {
            'email': request.user.email,
            'name': request.user.get_full_name() or request.user.email,
        },
        'meta': {
            'order_id': order.id,
        },
        'customizations': {
            'title': f'Payment for order #{order.id}',
            'description': f'Payment for {order.service.name} x {order.quantity}',
        },
    }

    response = requests.post(
        'https://api.flutterwave.com/v3/payments',
        headers={
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:
        return render(request, 'store/payment_status.html', {
            'order': order,
            'title': 'Payment Initialization Failed',
            'message': f'Could not start Flutterwave payment. ({response.status_code})',
            'success': False,
        })

    data = response.json()
    if data.get('status') != 'success' or not data.get('data'):
        error_message = data.get('message', 'Unable to initialize payment with Flutterwave.')
        return render(request, 'store/payment_status.html', {
            'order': order,
            'title': 'Payment Initialization Failed',
            'message': error_message,
            'success': False,
        })

    payment_link = data['data'].get('link')
    if not payment_link:
        return render(request, 'store/payment_status.html', {
            'order': order,
            'title': 'Payment Initialization Failed',
            'message': 'Flutterwave did not return a payment link.',
            'success': False,
        })

    return redirect(payment_link)

def verify_flutterwave_transaction(transaction_id=None, tx_ref=None):
    secret_key = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', None)
    if not secret_key or (not transaction_id and not tx_ref):
        return None

    if transaction_id:
        url = f'https://api.flutterwave.com/v3/transactions/{transaction_id}/verify'
    else:
        url = f'https://api.flutterwave.com/v3/transactions/verify_by_tx_ref?tx_ref={tx_ref}'

    response = requests.get(
        url,
        headers={
            'Authorization': f'Bearer {secret_key}',
        },
        timeout=30,
    )
    if response.status_code != 200:
        return None
    data = response.json()
    return data if data.get('status') == 'success' else None

def assign_accounts_to_user(user, platform, quantity, account_order):
    """Assign available social media accounts to the user after successful purchase"""
    available_accounts = SocialMediaAccount.objects.filter(
    platform=platform
    ).exclude(
        id__in=UserPlatformAccount.objects.values_list(
            'account_id',
            flat=True
        )
    )[:quantity]
    
    assigned_count = 0
    for account in available_accounts:
        UserPlatformAccount.objects.create(
            user=user,
            account=account,
            account_order=account_order
        )
        assigned_count += 1
    
    return assigned_count

def payment_callback(request, order_id):
    # Callback requests from Flutterwave may not preserve the user's session,
    # so do not require the callback to be authenticated. Locate the order
    # by its id only and then verify the transaction via Flutterwave.
    order = get_object_or_404(Order, id=order_id)
    transaction_id = request.GET.get('transaction_id')
    tx_ref = request.GET.get('tx_ref')
    status = request.GET.get('status')

    if transaction_id or tx_ref:
        verification = verify_flutterwave_transaction(transaction_id=transaction_id, tx_ref=tx_ref)
        if verification and verification.get('data', {}).get('status') in ('successful', 'completed'):
            order.status = 'completed'
            order.save()
            title = 'Payment Success'
            message = 'Payment completed successfully. Your order has been marked as completed.'
            success = True
            
            # call the-owlet API to process the order
            provider = TheOwletAPI()
            provider_response = provider.create_order(
                service_id=order.service.provider_service_id,
                link=order.target_link,
                quantity=order.quantity
            )
            order.provider_response = provider_response
            
            if provider_response.get('success'):
                order.provider_order_id = provider_response.get('provider_order_id')
                order.provider_status = 'pending'
                order.save()
            else:
                order.provider_order_id = provider_response.get('provider_order_id')
                order.provider_status = 'failed'
                order.save()
                title = 'Order Processing Failed'
                message = 'Payment was successful, but there was an issue processing your order with the provider. Please contact support.'
                success = False
            
        else:
            title = 'Payment Failed'
            message = 'Payment could not be verified. Your order remains pending.'
            success = False
    elif status in ('cancelled', 'failed', 'error'):
        title = 'Payment Failed'
        message = 'Payment was not completed. Your order remains pending.'
        success = False
    else:
        title = 'Payment Status Unknown'
        message = 'The payment result could not be determined. Please check your transaction status.'
        success = False

    return render(request, 'store/payment_status.html', {
        'order': order,
        'title': title,
        'message': message,
        'success': success,
    })

def get_service_price(request):
    service_id = request.GET.get('service_id')
    try:
        service = Service.objects.get(id=service_id)
        return JsonResponse({
            'price': str(service.price),
            'price_per_k': str(service.price_per_k or Decimal('0.00')),
        })
    except Service.DoesNotExist:
        return JsonResponse({'error': f'Service with ID {service_id} not found'}, status=404)
    
def calculate_total_price(request):
    service_id = request.GET.get('service_id')
    quantity = int(request.GET.get('quantity', 1))
    try:
        service = Service.objects.get(id=service_id)
        unit_price = service.price
        total_price = unit_price * quantity
        return JsonResponse({
            'total_price': str(total_price),
            'price_per_k': str(service.price_per_k or Decimal('0.00')),
            'price': str(unit_price),
            'quantity': str(quantity),
        })
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)

def orders(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/orders.html', {'orders': user_orders})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order-detail.html', {'order': order})

@login_required(login_url='login')
def admin_add_products(request):
    if request.user.role != 'admin':
        return redirect('home')
    
    form = SocialMediaAccountForm()
    if request.method == 'POST':
        form = SocialMediaAccountForm(request.POST)
        if form.is_valid():
            form_user = form.save(commit=False)
            form_user.user = request.user
            form_user.save()

            messages.success(request, 'Product added successfully.')
            return redirect('store:platform_list')
        else:
            error = next(iter(form.errors.values()))[0]
            messages.error(request, error)
            return redirect('store:add_products')
        
    return render(request, 'store/add-products.html', {'form': form})

@login_required(login_url='login')
def add_platform(request):
    if request.user.role != 'admin':
        return redirect('home')

    form = PlatformForm()
    if request.method == 'POST':
        form = PlatformForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Platform added successfully.')
            return redirect('store:platform_list')
        else:
            error = next(iter(form.errors.values()))[0]
            messages.error(request, error)
            return redirect('store:add_platform')
        
    return render(request, 'store/add-platform.html', {'form': form})

@login_required(login_url='login')
def view_platform(request, platform_id):
    platform = get_object_or_404(Platform, id=platform_id)
    return render(request, 'store/view-platform.html', {'platform': platform})

@login_required(login_url='login')
def edit_platform(request, platform_id):
    if request.user.role != 'admin':
        return redirect('home')

    platform = get_object_or_404(Platform, id=platform_id)
    form = PlatformForm(instance=platform)

    if request.method == 'POST':
        form = PlatformForm(request.POST, instance=platform)
        if form.is_valid():
            form.save()
            messages.success(request, 'Platform updated successfully.')
            return redirect('store:platform_list')
        else:
            error = next(iter(form.errors.values()))[0]
            messages.error(request, error)
            return redirect('store:edit_platform', platform_id=platform_id)

    return render(request, 'store/edit-platform.html', {'form': form, 'platform': platform})

@login_required(login_url='login')
def delete_platform(request, platform_id):
    if request.user.role != 'admin':
        return redirect('home')

    platform = get_object_or_404(Platform, id=platform_id)
    platform.delete()
    messages.success(request, 'Platform deleted successfully.')
    return redirect('store:platform_list')
    
@login_required(login_url='login')
def platform_list(request):
     
    platform = Platform.objects.all().order_by('-created_at')
    return render(request, 'store/product_list.html', {'products': platform})

@login_required(login_url='login')
def my_accounts(request):
    """Display accounts purchased by the user"""
    user_accounts = UserPlatformAccount.objects.filter(user=request.user).select_related('account', 'account_order')
    account_orders = AccountOrder.objects.filter(user=request.user, status='completed').order_by('-created_at')
    
    return render(request, 'store/my_accounts.html', {
        'user_accounts': user_accounts,
        'account_orders': account_orders,
    })

@login_required(login_url='login')
def purchase(request):
    if request.method == 'POST':
        platform_id = request.POST.get('platform_id')
        quantity = int(request.POST.get('quantity', 1))
        
        if not platform_id or quantity <= 0:
            return JsonResponse({'error': 'Invalid platform or quantity'}, status=400)
        
        try:
            platform = Platform.objects.get(id=platform_id)
        except Platform.DoesNotExist:
            return JsonResponse({'error': 'Platform not found'}, status=404)
        
        # Check if enough accounts are available
        available_accounts = SocialMediaAccount.objects.filter(
            platform=platform
        ).exclude(
            id__in=UserPlatformAccount.objects.values_list('account_id', flat=True)
        ).count()
        
        if available_accounts < quantity:
            return JsonResponse({
                'error': f'Only {available_accounts} accounts available for {platform.name}'
            }, status=400)
        
        # Create the order
        order = AccountOrder.objects.create(
            user=request.user,
            platform=platform,
            quantity=quantity,
            status='pending'
        )
        
        # Redirect to payment initialization
        return redirect('store:initialize_product_purchase', order_id=order.order_id)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required(login_url='login')
def initialize_product_purchase(request, order_id):
    order = get_object_or_404(AccountOrder, order_id=order_id, user=request.user)
    secret_key = getattr(settings, 'FLUTTERWAVE_SECRET_KEY')
    if not secret_key:
        return render(request, 'store/payment_status.html', {
            'order': order,
            'title': 'Payment Configuration Error',
            'message': 'Flutterwave secret key is missing. Please configure FLUTTERWAVE_SECRET_KEY.',
            'success': False,
        })
    tx_ref = f"boostivon-product-{order.order_id}-{uuid.uuid4().hex[:8]}"
    callback_url = request.build_absolute_uri(reverse('store:verify_product_payment', args=[order.order_id]))
    payload = {
        'tx_ref': tx_ref,
        'amount': str(order.total_price),
        'currency': 'NGN',
        'redirect_url': callback_url,
        'customer': {
            'email': request.user.email,
            'name': request.user.get_full_name() or request.user.email,
        },
        'meta': {
            'order_id': order.order_id,
        },
        'customizations': {
            'title': f'Payment for {order.platform.name} x {order.quantity}',
            'description': f'Payment for {order.platform.name} x {order.quantity}',
        },
    }
    response = requests.post(
        'https://api.flutterwave.com/v3/payments',
        headers={
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=30,
    )
    if response.status_code != 200:
        return render(request, 'store/payment_status.html', {
            'order': order,
            'title': 'Payment Initialization Failed',
            'message': f'Could not start Flutterwave payment. ({response.status_code})',
            'success': False,
        })
    data = response.json()
    if data.get('status') != 'success' or not data.get('data'):
        error_message = data.get('message', 'Unable to initialize payment with Flutterwave.')
        return render(request, 'store/payment_status.html', {
            'order': order,
            'title': 'Payment Initialization Failed',
            'message': error_message,
            'success': False,
        })
    payment_link = data['data'].get('link')
    if not payment_link:
        return render(request, 'store/payment_status.html', {
            'order': order,
            'title': 'Payment Initialization Failed',
            'message': 'Flutterwave did not return a payment link.',
            'success': False,
        })
    return redirect(payment_link)

def verify_product_payment(request, order_id):
    order = get_object_or_404(AccountOrder, order_id=order_id)
    platform = order.platform
    transaction_id = request.GET.get('transaction_id')
    tx_ref = request.GET.get('tx_ref')
    status = request.GET.get('status')
    if transaction_id or tx_ref:
        verification = verify_flutterwave_transaction(transaction_id=transaction_id, tx_ref=tx_ref)
        if verification and verification.get('data', {}).get('status') in ('successful', 'completed'):
            order.status = 'completed'
            order.save()
            
            # Assign accounts to user
            assigned_count = assign_accounts_to_user(order.user, platform, order.quantity, order)
            
            # Deduct from platform quantity
            platform.quantity -= assigned_count
            platform.save()
            
            title = 'Payment Success'
            message = f'Payment completed successfully. {assigned_count} {platform.name} accounts have been assigned to you.'
            success = True
        else:
            title = 'Payment Failed'
            message = 'Payment could not be verified. Your order remains pending.'
            success = False
    elif status in ('cancelled', 'failed', 'error'):
        title = 'Payment Failed'
        message = 'Payment was not completed. Your order remains pending.'
        success = False
    else:
        title = 'Payment Status Unknown'
        message = 'The payment result could not be determined. Please check your transaction status.'
        success = False
    return render(request, 'store/payment_status.html', {
        'order': order,
        'title': title,
        'message': message,
        'success': success,
    })
    