from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from rest_framework import status


class UserDetailApiTest(BaseUserTest):
    def test_user_detail(self):
        user = UserFactory(username='email@gmail.com')
        UserFactory(email='email2@gmail.com')

        data = {
            'username': 'email@gmail.com',
        }
        response = self.client.post(
            '/api/accounts/user_details/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], user.name)

    def test_user_detail_account_deactivated(self):
        UserFactory(username='email@gmail.com', is_active=False)
        data = {
            'username': 'email@gmail.com',
        }
        response = self.client.post(
            '/api/accounts/user_details/', data,
        )
        self.assertResponseStatus(response, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['message'], 'Your account has been deactivated.')
