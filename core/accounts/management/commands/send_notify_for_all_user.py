from django.core.management.base import BaseCommand

from core.accounts.models import User
from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE
from core.accounts.tasks.notification import make_notification_message


class Command(BaseCommand):
    help = 'Send a generic in-app notification to all users (uses NotificationTemplate GENERIC).'

    def handle(self, *args, **options):
        for user in User.objects.iterator():
            make_notification_message(
                user=user,
                content_code=NOTIFICATIONS_CONTENT_CODE.GENERIC,
                content_params={'message': 'PhotoBook: you have a new notification.'},
            )
        self.stdout.write(self.style.SUCCESS('Done.'))
