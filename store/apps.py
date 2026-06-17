from django.apps import AppConfig


class StoreConfig(AppConfig):
    name = 'store'
    
    def ready(self):
        import store.signals
        # start background scheduler for periodic tasks (exchange rate updates)
        try:
            from . import scheduler
            scheduler.start()
        except Exception:
            # avoid breaking app startup if scheduler cannot start
            pass
