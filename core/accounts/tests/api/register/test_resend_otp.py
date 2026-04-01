from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import get_random_string
from rest_framework import status

from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ResendOtpApiTests(BaseUserTest):
    @mock.patch('core.accounts.tasks.sms.send_sms_real.delay', autospec=True)
    def test_success(self, send_sms):
        user = UserFactory(is_active=False, phone_number='0909123456')
        otp_key = get_random_string(32)
        cache.set(f'register_opt_{user.id}', otp_key, settings.SMS_OPT_TIMEOUT)
        cache.set(otp_key, {'code': '123456', 'user_id': user.id}, settings.SMS_OPT_TIMEOUT)
        response = self.client.post(
            '/api/accounts/register/resend_otp/', {
                'key': user.register_otp_key,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_sms.assert_called_once()
        self.assertIsNotNone(cache.get(user.register_otp_key))

        response_throttle = self.client.post(
            '/api/accounts/register/resend_otp/', {
                'key': user.register_otp_key,
            },
        )
        self.assertEqual(response_throttle.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @mock.patch('core.accounts.tasks.sms.send_sms_real.delay', autospec=True)
    def test_invalid_key(self, send_sms):
        UserFactory(is_active=False, phone_number='0909123456')
        response = self.client.post(
            '/api/accounts/register/resend_otp/', {
                'key': get_random_string(32),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        send_sms.assert_not_called()

    @mock.patch('core.accounts.tasks.sms.send_sms_real.delay', autospec=True)
    def test_valid_key_no_user(self, send_sms):
        user = UserFactory(is_active=False, phone_number='0909123456')
        otp_key = get_random_string(32)
        cache.set(f'register_opt_{user.id}', otp_key, settings.SMS_OPT_TIMEOUT)
        cache.set(otp_key, {'code': '123456', 'user_id': user.id + 1}, settings.SMS_OPT_TIMEOUT)
        response = self.client.post(
            '/api/accounts/register/resend_otp/', {
                'key': otp_key,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        send_sms.assert_not_called()
