from unittest.mock import patch

from rest_framework import status

from core.accounts.factories.user import UserSignalIdFactory
from core.accounts.tests.api.base_user_test import BaseAdminTest


class UserAdminTest(BaseAdminTest):
    @patch('onesignal_sdk.request.httpx')
    def test_clear_user_signal_id(self, httpx):
        UserSignalIdFactory(user=self.user)
        self.assertEqual(self.user.signal_ids.count(), 1)
        httpx.request.return_value.status_code = 200
        httpx.request.return_value.content = b'{}'

        response = self.client.post(
            '/admin/accounts/user/', {
                'action': 'clear_one_signal_id',
                'select_across': 0,
                'index': 0,
                '_selected_action': self.user.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        self.assertEqual(self.user.signal_ids.count(), 0)
        httpx.request.assert_called_once()
        self.assertEqual(httpx.request.mock_calls[0].args[0], 'DELETE')
