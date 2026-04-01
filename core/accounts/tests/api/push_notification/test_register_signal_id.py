from uuid import uuid4

from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.factories.user import UserSignalIdFactory, UserFactory


class RegisterSignalIdApiTests(BaseUserTest):

    def test_register_one_signal_id(self):
        signal_id = str(uuid4())
        response = self.client.post(
            '/api/accounts/register_signal_id/', {
                'signal_id': signal_id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(signal_id, map(str, self.user.signal_ids.all().values_list('signal_id', flat=True)))

    def test_register_one_signal_id_same_user(self):
        signal_id = str(uuid4())
        UserSignalIdFactory(user=self.user, signal_id=signal_id)
        response = self.client.post(
            '/api/accounts/register_signal_id/', {
                'signal_id': signal_id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(signal_id, map(str, self.user.signal_ids.all().values_list('signal_id', flat=True)))

    def test_register_one_signal_id_same_device_different_user(self):
        self.user_2 = UserFactory()
        signal_id = str(uuid4())
        UserSignalIdFactory(user=self.user_2, signal_id=signal_id)
        response = self.client.post('/api/accounts/register_signal_id/', {
            'signal_id': signal_id,
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(signal_id, map(str, self.user.signal_ids.all().values_list('signal_id', flat=True)))
