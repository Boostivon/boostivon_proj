import json
import uuid
from decimal import Decimal

import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import CreateOrderForm, PlatformForm, SocialMediaAccountForm, ServiceForm
from .models import Platform, Service, Order, SocialMediaAccount, AccountOrder, UserPlatformAccount
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .providers.the_owlet import TheOwletAPI
from django.contrib.auth.decorators import login_required

# Create your views here.
def service_list(request):
    # Show list of services and allow admin to edit
    services = Service.objects.all().order_by('-created_at')
    return render(request, "store/service_list.html", {'services': services})


@login_required(login_url='login')
def edit_service(request, service_id):
    if request.user.role != 'admin':
        return redirect('home')

    service = get_object_or_404(Service, id=service_id)
    form = ServiceForm(instance=service)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated successfully.')
            return redirect('store:service_list')
        else:
            error = next(iter(form.errors.values()))[0]
            messages.error(request, error)
            return redirect('store:edit_service', service_id=service_id)

    return render(request, 'store/edit-service.html', {'form': form, 'service': service})

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
    # use wallet balance
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.user.wallet_balance >= order.total_price:
        order.status = 'completed'
        order.save()
        request.user.wallet_balance -= order.total_price
        request.user.save()
        
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
        
        messages.success(request, 'Payment successful using wallet balance. Your order is now completed.')
        return redirect('store:orders')
    
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
        # mark account as assigned so it's not available anymore
        account.is_assigned = True
        account.save()
        assigned_count += 1
    
    # recalculate platform quantity
    try:
        platform.save()
    except Exception:
        pass

    return assigned_count


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
            form.save()

            messages.success(request, 'Product added successfully.')
            return redirect('store:platform_list')
        else:
            error = next(iter(form.errors.values()))[0]
            messages.error(request, error)
            return redirect('store:add_products')
        
    return render(request, 'store/add-products.html', {'form': form})


@login_required(login_url='login')
def admin_order_issues(request):
    """Admin view to list all orders in the database."""
    if request.user.role != 'admin':
        return redirect('home')

    # Start with all orders, optimized with select_related
    issues = Order.objects.select_related('user', 'service').order_by('-created_at')

    # Apply filters
    order_id = request.GET.get('order_id', '').strip()
    status = request.GET.get('status', '').strip()

    if order_id:
        try:
            issues = issues.filter(id=int(order_id))
        except (ValueError, TypeError):
            pass

    if status:
        issues = issues.filter(provider_status=status)

    # Pagination: 50 items per page
    paginator = Paginator(issues, 50)
    page_num = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_num)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    # Get all unique statuses for filter dropdown
    all_statuses = Order.objects.values_list('provider_status', flat=True).distinct()

    return render(request, 'store/order_issues.html', {
        'page_obj': page_obj,
        'issues': page_obj.object_list,
        'all_statuses': all_statuses,
        'filter_order_id': order_id,
        'filter_status': status,
    })

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
    return render(request, 'store/platform_list.html', {'products': platform})

@login_required(login_url='login')
def product_list(request):
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('home')
    products = SocialMediaAccount.objects.all().order_by('-created_at')
    return render(request, 'store/product_list.html', {'products': products})

@login_required(login_url='login')
def product_detail(request, product_id):
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('home')
    product = get_object_or_404(SocialMediaAccount, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

@login_required(login_url='login')
def edit_product(request, product_id):
    if request.user.role != 'admin':
        return redirect('home')

    product = get_object_or_404(SocialMediaAccount, id=product_id)
    form = SocialMediaAccountForm(instance=product)

    if request.method == 'POST':
        form = SocialMediaAccountForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('store:product_list')
        else:
            error = next(iter(form.errors.values()))[0]
            messages.error(request, error)
            return redirect('store:edit_product', product_id=product_id)

    return render(request, 'store/edit-product.html', {'form': form, 'product': product})

@login_required(login_url='login')
def delete_product(request, product_id):
    if request.user.role != 'admin':
        return redirect('home')

    product = get_object_or_404(SocialMediaAccount, id=product_id)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('store:product_list')

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
            messages.error(request, 'Invalid platform or quantity')
            return redirect('store:platform_list')
        
        try:
            platform = Platform.objects.get(id=platform_id)
        except Platform.DoesNotExist:
            messages.error(request, 'Platform not found')
            return redirect('store:platform_list')
        
        # Check if enough accounts are available
        available_accounts = SocialMediaAccount.objects.filter(
            platform=platform
        ).exclude(
            id__in=UserPlatformAccount.objects.values_list('account_id', flat=True)
        ).count()
        
        if available_accounts < quantity:
            messages.error(request, f'Only {available_accounts} accounts available for {platform.name}')
            return redirect('store:view_platform', platform_id=platform.id)
        
        # Create the order
        order = AccountOrder.objects.create(
            user=request.user,
            platform=platform,
            quantity=quantity,
            status='pending'
        )
        
        # Redirect to payment initialization
        return redirect('store:initialize_product_purchase', order_id=order.order_id)
    
    messages.error(request, 'Invalid request method')
    return redirect('store:platform_list')

@login_required(login_url='login')
def initialize_product_purchase(request, order_id):
    # use wallet balance
    order = get_object_or_404(AccountOrder, order_id=order_id, user=request.user)
    if request.user.wallet_balance >= order.total_price:
        order.status = 'completed'
        order.save()
        request.user.wallet_balance -= order.total_price
        request.user.save()
        
        # Assign accounts to user
        assigned_count = assign_accounts_to_user(order.user, order.platform, order.quantity, order)
        
        title = 'Purchase Successful'
        message = f'Purchase completed successfully. {assigned_count} {order.platform.name} accounts have been assigned to you.'
        success = True
        
        messages.success(request, message)
        return redirect('store:my_accounts')
    else:
        messages.error(request, 'Insufficient wallet balance. Please fund your wallet to complete the purchase.')
        return redirect('fund_wallet')
    
@login_required(login_url='login')
def admin_order_detail(request, order_id):
    if request.user.role != 'admin':
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('home')
    
    if not order_id:
        messages.error(request, 'Order ID is required.')
        return redirect('home')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('home')

    return render(request, 'store/admin_order_detail.html', {'order': order})

def terms_and_conditions(request):
    return render(request, 'store/terms-and-conditions.html')