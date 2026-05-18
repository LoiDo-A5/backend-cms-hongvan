from django.conf import settings
from celery import shared_task
from onesignal_sdk.client import Client
from core.accounts.models.notification import Notification
from core.accounts.ultils.notifications.get_notification_template import get_notification_template


default_credentials = {
    'rest_api_key': settings.ONESIGNAL_APP_KEY,
    'app_id': settings.ONESIGNAL_APP_ID,
    # 'android_channel_id': settings.ONESIGNAL_ANDROID_CHANNEL_ID,
}


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 5}, queue='notification')
def send_one_signal_notification(user_id, title, message, credentials=None, **options):
    send_one_signal_notification_to_many_users(
        [user_id], title, message, credentials=credentials,
        **options,
    )


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def send_one_signal_notification_to_many_users(
        user_ids, title, message, credentials=None, **options,
):
    from core.accounts.models import UserSignalId

    signal_ids = UserSignalId.objects.filter(user__in=user_ids).values_list('signal_id', flat=True)
    signal_ids = [str(x) for x in signal_ids]
    send_notification_to_signal_ids(
        signal_ids, title=title, message=message, credentials=credentials, **options,
    )


def send_notification_to_signal_ids(signal_ids, message, title, credentials=None, **options):
    if not signal_ids:
        return

    title = {'en': title} if isinstance(title, str) else title
    message = {'en': message} if isinstance(message, str) else message
    credentials = credentials or default_credentials

    onesignal_client = Client(
        rest_api_key=credentials['rest_api_key'],
        app_id=credentials['app_id'],
    )

    new_notification = {
        'contents': message,
        'headings': title,
        'include_player_ids': signal_ids,
        'android': {
            'priority': 'high',
        },
        'priority': 10,
        'content_available': True,
        # 'android_channel_id': credentials['android_channel_id'],
    }

    new_notification.update(options)

    onesignal_client.send_notification(new_notification)


def make_notification_message(
        user, content_code, content_params=None, notification_kwargs=None,
        push_kwargs=None, credentials=None,
):
    push_kwargs = push_kwargs or {}
    notification_kwargs = notification_kwargs or {}
    content_params = content_params or {}

    template = get_notification_template(content_code)

    if not template:
        return

    notification = Notification.objects.create(
        template=template,
        user=user,
        params=content_params,
        push_kwargs=push_kwargs,
        content_code=content_code,
        **notification_kwargs,
    )

    user.send_notification(
        title=template.title_en,
        message=notification.content_en,
        credentials=credentials,
        **push_kwargs,
    )
