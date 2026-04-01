from django.test import TestCase

from core.accounts.ultils.notifications.get_notification_template import get_notification_template
from core.accounts.tasks.notification import make_notification_message
from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE
from core.accounts.factories.user import UserFactory
from core.accounts.models.notification import Notification


class GetNotificationTemplateTests(TestCase):
    def test_get_notification_template(self):
        template = get_notification_template(content_code=NOTIFICATIONS_CONTENT_CODE.GENERIC)

        self.assertIsNotNone(template)

    def test_should_response_none_when_pass_wrong_code(self):
        template = get_notification_template(content_code='WRONG_CODE')
        self.assertIsNone(template)

    def test_make_notification_should_not_create_new_notification_if_pass_wrong_code(self):
        user = UserFactory()
        self.assertEqual(Notification.objects.count(), 0)

        make_notification_message(user=user, content_code='WRONG_CODE')

        self.assertEqual(Notification.objects.count(), 0)
