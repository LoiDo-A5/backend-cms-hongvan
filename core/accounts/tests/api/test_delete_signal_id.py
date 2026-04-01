from core.accounts.factories.user import UserSignalIdFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from rest_framework import status
from uuid import uuid4


class DeleteSignalIDApiTest(BaseUserTest):
    def test_user_detail(self):
        signal_id = str(uuid4())
        UserSignalIdFactory(user=self.user, signal_id=signal_id)

        data = {
            'signal_id': signal_id,
        }
        response = self.client.post(
            '/api/accounts/delete_signal_id/', data,
        )

        self.assertResponseStatus(response, status.HTTP_204_NO_CONTENT)
