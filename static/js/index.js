import Swal from './vendor/sweetalert2.esm.all.min.js';

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

    // search users in admin users page using ajax

    $('#user-search').on('input', function() {
        const query = $(this).val();
        $.ajax({
            url: '/search-users/',
            method: 'GET',
            data: {
                'q': query
            },
            success: function(response) {
                const users = response.users;
                const tbody = $('#users-table-body');
                tbody.empty();
                if (users.length > 0) {
                    users.forEach(user => {
                        const row = `<tr>
                            <td>${user.username}</td>
                            <td>${user.email}</td>
                            <td class="text-right">₦${parseFloat(user.wallet_balance).toFixed(2)}</td>
                            <td class="text-right">${user.total_orders ?? 0}</td>
                            <td><span class="badge active">${user.role}</span></td>
                        </tr>`;
                        tbody.append(row);
                    });
                } else {
                    tbody.append('<tr><td colspan="5" class="text-center">No users found</td></tr>');
                }
            },
            error: function(xhr) {
                Toast.fire({
                    icon: 'error',
                    title: 'Failed to search users'
                });
            }
        });
    });
    
});
