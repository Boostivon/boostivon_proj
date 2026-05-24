from django.urls import path

from store.views import (
    calculate_total_price,
    create_order,
    get_service_price,
    initialize_payment,
    order_detail,
    payment_callback,
    service_list,
    orders,
)

app_name = 'store'

urlpatterns = [
    path('services/', service_list, name='service_list'),
    path('order/new/', create_order, name='create_order'),
    path('order/<int:order_id>/detail/', order_detail, name='order_detail'),
    path('orders/', orders, name="orders"),
    path('get-service-price/', get_service_price, name='get_service_price'),
    path('calculate-total-price/', calculate_total_price, name='calculate_total_price'),
    path('payment/initiate/<int:order_id>/', initialize_payment, name='initialize_payment'),
    path('payment/callback/<int:order_id>/', payment_callback, name='payment_callback'),
]