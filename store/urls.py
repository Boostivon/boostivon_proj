from django.urls import path

from store.views import (
    add_platform,
    admin_add_products,
    calculate_total_price,
    create_order,
    delete_platform,
    edit_platform,
    get_service_price,
    initialize_payment,
    order_detail,
    payment_callback,
    platform_list,
    service_list,
    orders,
    view_platform,
    purchase,
    initialize_product_purchase,
    verify_product_payment,
    my_accounts,
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
    path('add-products/', admin_add_products, name='add_products'),
    path('add-platform/', add_platform, name='add_platform'),
    path('platforms/', platform_list, name='platform_list'),
    path('edit-platform/<int:platform_id>/', edit_platform, name='edit_platform'),
    path('delete-platform/<int:platform_id>/', delete_platform, name='delete_platform'),
    path('view-platform/<int:platform_id>/', view_platform, name='view_platform'),
    path('purchase/', purchase, name='purchase'),
    path('purchase/initialize/<uuid:order_id>/', initialize_product_purchase, name='initialize_product_purchase'),
    path('purchase/verify/<uuid:order_id>/', verify_product_payment, name='verify_product_payment'),
    path('my-accounts/', my_accounts, name='my_accounts'),
]