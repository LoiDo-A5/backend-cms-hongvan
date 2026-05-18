import pusher
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from sentry_sdk import capture_exception

pusher_client = None


def get_pusher():
    global pusher_client
    if pusher_client is None:
        pusher_client = pusher.Pusher(
            app_id=settings.PUSHER_APP_ID,
            key=settings.PUSHER_APP_KEY,
            secret=settings.PUSHER_APP_SECRET,
            cluster=settings.PUSHER_APP_CLUSTER,
            ssl=True,
        )
    return pusher_client


def pusher_client_trigger(channels, event_name, data, socket_id=None):
    real_pusher_trigger.delay(channels, event_name, data, socket_id=socket_id)


@shared_task
def real_pusher_trigger(channels, event_name, data, socket_id=None):
    try:
        get_pusher().trigger(channels, event_name, data, socket_id=socket_id)
    except Exception as err:
        name_error = type(err).__name__
        if not cache.get(f'PusherError_{event_name}_{name_error}'):
            capture_exception(err)
            cache.set(f'PusherError_{event_name}_{name_error}', True, 86400)
