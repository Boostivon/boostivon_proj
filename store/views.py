import json
import uuid
from decimal import Decimal

import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import CreateOrderForm
from .models import Service, Order
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

