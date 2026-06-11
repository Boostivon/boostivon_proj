document.addEventListener('DOMContentLoaded', function () {
  const purchaseForm = document.getElementById('purchase-form');
  const quantityInput = document.getElementById('quantity');
  const totalPriceEl = document.getElementById('total-price');

  if (!purchaseForm || !quantityInput || !totalPriceEl) {
    return;
  }

  const maxQuantity = parseInt(purchaseForm.dataset.max || '0', 10);
  const pricePerAccount = parseFloat(purchaseForm.dataset.price || '0');

  function updateTotal() {
    const quantity = Math.max(1, Math.min(maxQuantity, parseInt(quantityInput.value, 10) || 1));
    const total = quantity * pricePerAccount;
    totalPriceEl.textContent = '₦' + total.toFixed(2);
  }

  function increaseQuantity() {
    const currentQuantity = parseInt(quantityInput.value, 10) || 1;
    if (currentQuantity < maxQuantity) {
      quantityInput.value = currentQuantity + 1;
      updateTotal();
    }
  }

  function decreaseQuantity() {
    const currentQuantity = parseInt(quantityInput.value, 10) || 1;
    if (currentQuantity > 1) {
      quantityInput.value = currentQuantity - 1;
      updateTotal();
    }
  }

  window.increaseQuantity = increaseQuantity;
  window.decreaseQuantity = decreaseQuantity;

  updateTotal();

  purchaseForm.addEventListener('submit', function (e) {
    const quantity = parseInt(quantityInput.value, 10) || 0;
    if (quantity < 1 || quantity > maxQuantity) {
      e.preventDefault();
      alert('Please select a valid quantity');
    }
  });
});
