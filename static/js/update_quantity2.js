document.addEventListener('DOMContentLoaded', function () {
  const purchaseForm = document.getElementById('purchase-form');
  const quantityInput = document.getElementById('quantity');
  const totalPriceEl = document.getElementById('total-price');
  const adjustedPriceSource = document.getElementById('hello');
  const totalPriceInput = document.getElementById('total_price_input');

  if (!purchaseForm || !quantityInput || !totalPriceEl || !adjustedPriceSource || !totalPriceInput) {
    return;
  }

  const maxQuantity = parseInt(purchaseForm.dataset.max || '0', 10);

  function getPricePerAccount() {
    const datasetPrice = parseFloat(adjustedPriceSource.dataset.adjustedPrice || '0');
    const sourceText = parseFloat(adjustedPriceSource.textContent || '0');
    return !Number.isNaN(datasetPrice) && datasetPrice > 0 ? datasetPrice : (!Number.isNaN(sourceText) && sourceText > 0 ? sourceText : 0);
  }

  function updateSmPlatformTotal() {
    const quantity = Math.max(1, Math.min(maxQuantity, parseInt(quantityInput.value, 10) || 1));
    const pricePerAccount = getPricePerAccount();
    const total = quantity * pricePerAccount;
    totalPriceEl.textContent = '₦' + total.toFixed(2);
    totalPriceInput.value = total.toFixed(2);
  }

  function handleAdjustedPriceReady() {
    updateSmPlatformTotal();
  }

  document.addEventListener('adjustedPriceReady', handleAdjustedPriceReady);

  function increaseSmPlatformQuantity() {
    const currentQuantity = parseInt(quantityInput.value, 10) || 1;
    if (currentQuantity < maxQuantity) {
      quantityInput.value = currentQuantity + 1;
      updateSmPlatformTotal();
    }
  }

  function decreaseSmPlatformQuantity() {
    const currentQuantity = parseInt(quantityInput.value, 10) || 1;
    if (currentQuantity > 1) {
      quantityInput.value = currentQuantity - 1;
      updateSmPlatformTotal();
    }
  }

  window.increaseSmPlatformQuantity = increaseSmPlatformQuantity;
  window.decreaseSmPlatformQuantity = decreaseSmPlatformQuantity;

  updateSmPlatformTotal();

  purchaseForm.addEventListener('submit', function (e) {
    const quantity = parseInt(quantityInput.value, 10) || 0;
    if (quantity < 1 || quantity > maxQuantity) {
      e.preventDefault();
      alert('Please select a valid quantity');
    }
  });
});
