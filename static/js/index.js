import Swal from  './node_modules/sweetalert2/src/sweetalert2.js';

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(document).ready(function() {
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
    });

    $(document).on('click', '#send-verification', function(e) {
        e.preventDefault();
        
        $.ajax({
            url: '/send-verification/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                Toast.fire({
                    icon: 'success',
                    title: 'Verification email sent'
                });
                location.replace('/verify-email/');
            },
            error: function(xhr) {
                Toast.fire({
                    icon: 'error',
                    title: 'Failed to send verification email'
                });
                console.error('Error:', xhr.responseText);
            }
        });
    });

    // update pricing based on service selection
    $('#id_service').on('change', function() {
        const serviceId = $(this).val();
        const quantity = parseInt($('#id_quantity').val() || 1, 10);
        if (serviceId) {
            $.ajax({
                url: '/store/get-service-price/',
                method: 'GET',
                data: {
                    'service_id': serviceId
                },
                success: function(response) {
                    const price = response.price;
                    const pricePerK = response.price_per_k;
                    const totalPrice = (quantity > 0) ? (parseFloat(price) * quantity).toFixed(2) : '';

                    $('input[name="total_price_"]').val(`₦${totalPrice}`);
                    $('#id_total_preview').text(totalPrice ? `₦${totalPrice}` : '');
                    $('#id_price_per_k').text(`₦${parseFloat(pricePerK).toFixed(2)}`);
                    $('#id_quantity_preview').text(quantity);

                    Toast.fire({
                        icon: 'success',
                        title: 'Service price updated'
                    });
                },
                error: function(xhr) {
                    Toast.fire({
                        icon: 'error',
                        title: xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : 'Failed to fetch service price'
                    });
                }
            });
        }
    });

    // update total price based on quantity input
    $('#id_quantity').on('input', function() {
        const quantity = parseInt($(this).val(), 10);
        const serviceId = $('#id_service').val();
        if (serviceId && quantity > 0) {
            $.ajax({
                url: '/store/calculate-total-price/',
                method: 'GET',
                data: {
                    'service_id': serviceId,
                    'quantity': quantity
                },
                success: function(response) {
                    $('input[name="total_price_"]').val(`₦${response.total_price}`);
                    $('#id_total_preview').text(`₦${response.total_price}`);
                    $('#id_price_per_k').text(`₦${response.price_per_k}`);
                    $('#id_quantity_preview').text(response.quantity);
                },
                error: function(xhr) {
                    Toast.fire({
                        icon: 'error',
                        title: xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : 'Failed to calculate total price'
                    });
                }
            });
        }
    });
    
});
