from unittest import mock

import requests_mock
from django.core.cache import cache
from rest_framework import status

from common.tests.isolated_cache_test_case import APITestCase
from core.accounts.factories.user import UserFactory
from core.accounts.utils import otp_generator


class ForgotPasswordTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.user_1 = UserFactory()
        cls.user_id = cls.user.id

    @mock.patch('core.accounts.tasks.sms.requests')
    def test_throttle_send_opt(self, requests):
        requests.get.return_value.json.return_value = {
            'CodeResult': '100',
        }
        response = self.client.post(
            '/api/accounts/forgot_password/',
            data={'username': self.user.username},
            format='json',
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)

        response_throttle = self.client.post(
            '/api/accounts/forgot_password/',
            data={'username': self.user.username},
            format='json',
        )
        self.assertEqual(response_throttle.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        response_1 = self.client.post(
            '/api/accounts/forgot_password/',
            data={'username': self.user_1.username},
            format='json',
        )
        self.assertEqual(response_1.status_code, status.HTTP_200_OK, response.content)

    @mock.patch('core.accounts.api.forgot_password.forgot_password.UserSendOtpThrottle.allow_request')
    def test_forgot_password_success(self, throttle):
        throttle.allow_request = True

        with requests_mock.Mocker() as m:
            m.get('http://rest.esms.vn/MainService.svc/json/SendMultipleMessage_V4_get', json={
                'CodeResult': '100',
            })
            response = self.client.post(
                '/api/accounts/forgot_password/',
                data={'username': self.user.username},
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(m.request_history), 1)
        self.assertNotEqual(self.user.forgot_password_data['otp'], '')
        self.assertFalse(self.user.forgot_password_data['is_verified'])

    @mock.patch('core.accounts.api.forgot_password.forgot_password.UserSendOtpThrottle.allow_request')
    def test_forgot_password_error_user_does_not_exist(self, throttle):
        throttle.return_value = True
        response = self.client.post(
            '/api/accounts/forgot_password/', data={
                'username': 'abc',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {'non_field_errors': ['Account does not exist']},
        )

    def test_forgot_password_verify_otp(self):
        user = self.user

        otp = otp_generator()
        user.set_forgot_password_data({'otp': otp, 'is_verified': False})

        response = self.client.post(
            '/api/accounts/forgot_password/verify_otp/', data={
                'username': user.username,
                'forgot_password_otp': otp,
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertTrue(user.forgot_password_data['is_verified'])
        self.assertEqual(user.forgot_password_data['otp'], '')

    def test_forgot_password_verify_otp_not_enough_length(self):
        self.user.set_forgot_password_data({'otp': '123456', 'is_verified': False})
        response = self.client.post(
            '/api/accounts/forgot_password/verify_otp/', data={
                'username': self.user.username,
                'forgot_password_otp': '123',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {'forgot_password_otp': ['Ensure this field has at least 6 characters.']},
        )

    def test_forgot_password_verify_otp_error_user_does_not_exist(self):
        self.user.set_forgot_password_data({'otp': '123456', 'is_verified': False})
        response = self.client.post(
            '/api/accounts/forgot_password/verify_otp/', data={
                'username': 'abc',
                'forgot_password_otp': '123456',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {'non_field_errors': ['Account does not exist']},
        )

    def test_forgot_password_verify_otp_error_otp_has_been_verified(self):
        self.user.set_forgot_password_data({'otp': '', 'is_verified': True})
        response = self.client.post(
            '/api/accounts/forgot_password/verify_otp/', data={
                'username': self.user.username,
                'forgot_password_otp': '123456',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {'non_field_errors': ['Your OTP has been verified']},
        )

    def test_forgot_password_verify_otp_error_have_not_requested_forgot_password(self):
        self.user.set_forgot_password_data({'otp': '', 'is_verified': False})
        response = self.client.post(
            '/api/accounts/forgot_password/verify_otp/', data={
                'username': self.user.username,
                'forgot_password_otp': '123456',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {'non_field_errors': ['You have not requested to forgot password']},
        )

    def test_forgot_password_verify_otp_error_otp_not_match(self):
        self.user.set_forgot_password_data({'otp': '123456', 'is_verified': False})
        response = self.client.post(
            '/api/accounts/forgot_password/verify_otp/', data={
                'username': self.user.username,
                'forgot_password_otp': '654321',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {'forgot_password_otp': ['Incorrect OTP']},
        )

    def test_forgot_password_set_password(self):
        user = self.user
        user.is_active = False
        user.save()
        user.set_forgot_password_data({'otp': '', 'is_verified': True})

        response = self.client.post(
            '/api/accounts/forgot_password/set_password/', data={
                'username': self.user.username,
                'password': 'new_password',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password('new_password'))
        self.assertEqual(user.forgot_password_data['otp'], '')
        self.assertFalse(user.forgot_password_data['is_verified'])

    def test_forgot_password_set_password_error_user_does_not_exist(self):
        response = self.client.post(
            '/api/accounts/forgot_password/set_password/', data={
                'username': 'abc',
                'password': 'new_password',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {'non_field_errors': ['Account does not exist']},
        )

    def test_forgot_password_set_password_error_otp_not_verified(self):
        self.user.set_forgot_password_data({'otp': '123456', 'is_verified': False})
        response = self.client.post(
            '/api/accounts/forgot_password/set_password/', data={
                'username': self.user.username,
                'password': 'new_password',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {'non_field_errors': ['Please verify OTP first']},
        )

    def test_forgot_password_set_password_error_verified_but_otp_is_not_valid(self):
        self.user.set_forgot_password_data({'otp': '123456', 'is_verified': True})
        response = self.client.post(
            '/api/accounts/forgot_password/set_password/', data={
                'username': self.user.username,
                'password': 'new_password',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {'non_field_errors': ['Verified but OTP is not valid']},
        )

    def test_delete_user_and_cache(self):
        self.user.set_forgot_password_data({'otp': '123456', 'is_verified': False})
        self.user.delete()
        self.assertIsNone(cache.get(self.user.forgot_password_key))
