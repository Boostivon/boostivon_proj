const conversionUrl = '/convert-price/';

async function convertToNaira(amount) {
    try {
        const url = `${conversionUrl}?amount=${encodeURIComponent(amount)}`;
        const response = await fetch(url, { method: 'GET', credentials: 'same-origin' });
        if (!response.ok) {
            throw new Error(`Conversion request failed (${response.status})`);
        }
        const data = await response.json();
        const converted = parseFloat(data.price_in_naira);
        return Number.isNaN(converted) ? amount : converted;
    } catch (error) {
        console.error('Currency conversion failed:', error);
        return amount;
    }
}


function calculateMarkedUpPrice(nairaPrice) {
    if (nairaPrice >= 40100) {
        nairaPrice += nairaPrice * 0.1;
        return nairaPrice;
    }
    if (nairaPrice >= 20100) {
        nairaPrice += nairaPrice * 0.2;
        return nairaPrice;
    }
    if (nairaPrice >= 10100) {
        nairaPrice += nairaPrice * 0.3;
        return nairaPrice;
    }
    if (nairaPrice >= 6100) {
        nairaPrice += nairaPrice * 0.5;
        return nairaPrice;
    }
    if (nairaPrice >= 3100) {
        nairaPrice += nairaPrice * 0.75;
        return nairaPrice;
    }
    if (nairaPrice >= 1000 || nairaPrice < 1000) {
        nairaPrice += nairaPrice;
        return nairaPrice;
    }
    return nairaPrice;
}
console.log(calculateMarkedUpPrice(20100))

document.addEventListener('DOMContentLoaded', () => {
    const priceElements = document.querySelectorAll('.price[data-price]');
    // get input with name platform_price
    let totalPriceEl = document.getElementById('hello');

    priceElements.forEach(element => {
        const price = parseFloat(element.getAttribute('data-price'));
        if (Number.isNaN(price)) {
            element.innerHTML = 'N/A';
            return;
        }

        element.innerHTML = 'Loading…';

        (async () => {
            const nairaPrice = await convertToNaira(price);
            const adjustedPrice = calculateMarkedUpPrice(nairaPrice);
            // add comma separators for thousands
            element.innerHTML = `₦${adjustedPrice.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,')} Each`;
            totalPriceEl.textContent = adjustedPrice.toFixed(2);
            totalPriceEl.dataset.adjustedPrice = adjustedPrice.toFixed(2);
            document.dispatchEvent(new CustomEvent('adjustedPriceReady', { detail: { adjustedPrice } }));
            console.log(totalPriceEl.textContent);
            console.log(`Converted price:${price} ${nairaPrice} → ₦${adjustedPrice}`);
        })();
    });
});
