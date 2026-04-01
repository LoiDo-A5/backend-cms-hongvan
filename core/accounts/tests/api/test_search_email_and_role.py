from rest_framework import status

from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class SearchUserByEmailAndRoleApiTests(BaseUserTest):
    def test_search_email_and_role_success(self):
        UserFactory(email='email123@gmail.com', role=1)
        UserFactory(email='email1234@gmail.com', role=2)
        UserFactory(email='email1235@gmail.com', role=3)

        data = {
            'email': 'email123@gmail.com',
            'role': '1,2',
        }
        response = self.client.get(
            '/api/accounts/search_email_and_role/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)

    def test_search_email_and_role_no_matching_role(self):
        UserFactory(email='email123@gmail.com', role=1)
        UserFactory(email='email1234@gmail.com', role=2)
        UserFactory(email='email1235@gmail.com', role=3)

        data = {
            'email': 'email123@gmail.com',
            'role': '2,3',
        }

        response = self.client.get('/api/accounts/search_email_and_role/', data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Email exists but the user does not have the requested roles. Please search again.',
                      response.json()['message'])

    def test_search_email_case_email_required(self):
        UserFactory(email='email123@gmail.com', role=1)
        data = {
            'role': '1,2',
        }
        response = self.client.get(
            '/api/accounts/search_email_and_role/', data,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Email is required',
                      response.json()['message'])

    def test_search_for_yourself(self):
        data = {
            'email': self.user.email,
            'role': self.user.role,
        }
        response = self.client.get(
            '/api/accounts/search_email_and_role/', data,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('You cannot search for yourself.',
                      response.json()['message'])

    def test_search_with_role_request_is_1(self):
        data = {
            'email': self.user.email,
            'role': self.user.role,
            'role_request': '1',
        }
        response = self.client.get(
            '/api/accounts/search_email_and_role/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
