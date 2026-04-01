from faker import Faker
from django.utils import timezone

from core.accounts.factories.notification import NotificationFactory
from core.accounts.tests.api.base_user_test import BaseUserTest

faker = Faker()


class NotificationApiTest(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_get_list_notification(self):
        notification_1 = NotificationFactory(user=self.user)
        notification_2 = NotificationFactory(user=self.user)

        NotificationFactory()

        response = self.client.get('/api/accounts/notification/', format='json')
        results = response.data

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], notification_2.id)
        self.assertEqual(results[1]['id'], notification_1.id)

    def test_notification_number(self):
        NotificationFactory(user=self.user, is_read=True)
        NotificationFactory(user=self.user)

        NotificationFactory()

        response = self.client.get('/api/accounts/notification/number/', format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'unread': 1, 'unseen': 1})

    def test_get_notification_number_has_last_seen_notification(self):
        NotificationFactory(user=self.user)
        NotificationFactory(user=self.user)
        last_seen_notification = timezone.now()
        self.user.last_seen_notification_at = last_seen_notification
        self.user.save()
        notification = NotificationFactory(user=self.user)  # unseen

        response = self.client.get('/api/accounts/notification/number/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'unread': 3, 'unseen': 1})

        self.client.post(f'/api/accounts/notification/{notification.id}/set_read/')
        response = self.client.get('/api/accounts/notification/number/')
        self.assertEqual(response.data, {'unread': 2, 'unseen': 0})

    def test_notifications_set_read(self):
        notification = NotificationFactory(user=self.user)
        response = self.client.post(f'/api/accounts/notification/{notification.id}/set_read/')
        self.assertEqual(response.status_code, 200)

    def test_notifications_set_read_case_notification_already_read(self):
        notification = NotificationFactory(user=self.user, is_read=True)
        response = self.client.post(f'/api/accounts/notification/{notification.id}/set_read/')
        self.assertEqual(response.status_code, 204)

    def test_set_last_seen_notification(self):
        self.assertIsNone(self.user.last_seen_notification_at)
        response = self.client.post('/api/accounts/notification/set_last_seen/')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_seen_notification_at)
