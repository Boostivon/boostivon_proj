import requests
from decimal import Decimal
from django.conf import settings

from .models import ExchangeRate


def update_exchange_rate(from_currency='USD', to_currency='NGN'):
    """Fetch latest rate and store in DB. Returns Decimal rate or None."""
    # Use ExchangeRate-API (open.er-api.com) which provides free latest rates
    url = f"https://open.er-api.com/v6/latest/{from_currency}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"update_exchange_rate: non-200 status: {resp.status_code} - {resp.text}")
            return None
        data = resp.json()
        rate = data.get('rates', {}).get(to_currency)
        if rate is None:
            print(f"update_exchange_rate: no rate in response: {data}")
            return None
        rate_dec = Decimal(str(rate))
        ExchangeRate.objects.update_or_create(
            from_currency=from_currency,
            to_currency=to_currency,
            defaults={"rate": rate_dec}
        )
        return rate_dec
    except Exception as e:
        print(f"update_exchange_rate: exception: {e}")
        return None


def get_exchange_rate(from_currency='USD', to_currency='NGN'):
    """Return Decimal exchange rate. If not present, try to update once, otherwise return Decimal('1')."""
    try:
        er = ExchangeRate.objects.filter(from_currency=from_currency, to_currency=to_currency).order_by('-updated_at').first()
        if er and er.rate:
            return Decimal(er.rate)
        # try updating once
        updated = update_exchange_rate(from_currency, to_currency)
        if updated:
            return Decimal(updated)
    except Exception:
        pass
    return Decimal('1')
