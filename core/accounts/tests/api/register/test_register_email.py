from rest_framework import status

from core.accounts.factories.user import UserFactory
from core.accounts.models import User
from core.accounts.tests.api.base_user_test import BaseUserTest


class RegisterEmailApiTests(BaseUserTest):
    def test_register_email_success(self):
        data = {
            'email': 'email123@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.client.post(
            '/api/accounts/register/email/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.user.refresh_from_db()
        new_user = User.objects.get(email='email123@gmail.com')
        self.assertIsNone(new_user.phone_number)
        self.assertEqual(new_user.time_zone, 'Asia/Jakarta')

    def test_register_phone_success(self):
        data = {
            'phone_number': '0909777xxx',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.client.post(
            '/api/accounts/register/email/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.user.refresh_from_db()
        new_user = User.objects.get(phone_number='0909777xxx')
        self.assertIsNone(new_user.email)
        self.assertEqual(new_user.time_zone, 'Asia/Jakarta')

    def test_password_not_match(self):
        data = {
            'email': 'email123@gmail.com',
            'password1': 'abc',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.client.post(
            '/api/accounts/register/email/', data,
        )

        self.assertResponseStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'][0], "The two password fields didn't match.")

    def test_register_with_existed_email(self):
        existing = UserFactory()
        data = {
            'email': existing.email,
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.client.post(
            '/api/accounts/register/email/', data,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'], ['Email address already in use'])

    def test_register_with_existed_phone_number(self):
        existing = UserFactory()
        data = {
            'phone_number': existing.phone_number,
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.client.post(
            '/api/accounts/register/email/', data,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['phone_number'], ['Phone number already in use'])

    def test_register_email_no_timezone_provided(self):
        data = {
            'email': 'email123@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
        }
        response = self.client.post(
            '/api/accounts/register/email/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        user = User.objects.get(email='email123@gmail.com')
        self.assertEqual(user.time_zone, 'Asia/Ho_Chi_Minh')
