from django.core.management.base import BaseCommand

from store.utils import update_exchange_rate


class Command(BaseCommand):
    help = 'Updates USD to NGN exchange rate'

    def handle(self, *args, **kwargs):
        rate = update_exchange_rate()
        if rate:
            self.stdout.write(self.style.SUCCESS(f"Rate updated: {rate}"))
        else:
            self.stdout.write(self.style.ERROR("Failed to update rate"))
