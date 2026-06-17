from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings

from .utils import update_exchange_rate

_scheduler = None

def start():
    global _scheduler
    if _scheduler:
        return
    scheduler = BackgroundScheduler()
    # default: update USD->NGN every hour
    scheduler.add_job(lambda: update_exchange_rate('USD', 'NGN'), 'interval', hours=1, id='update_usd_ngn_rate')
    scheduler.start()
    _scheduler = scheduler

def shutdown():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
