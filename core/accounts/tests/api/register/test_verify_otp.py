from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import get_random_string
from rest_framework import status

from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class VerifyPhoneTests(BaseUserTest):

    def call_api_verify_otp(self, code, otp_key):
        return self.client.post(
            '/api/accounts/register/verify_otp/', {
                'code': code,
                'otp_key': otp_key,
            },
        )

    def _set_otp(self, user, key):
        otp_key = get_random_string(32)
        cache.set(f'register_opt_{user.id}', otp_key, settings.SMS_OPT_TIMEOUT)
        cache.set(user.register_otp_key, {'code': key, 'user_id': user.id}, settings.SMS_OPT_TIMEOUT)
        return otp_key

    def test_invalid_otp(self):
        user = UserFactory(is_phone_verified=False)
        otp_key = self._set_otp(user, '123457')
        response = self.call_api_verify_otp('123456', otp_key)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid OTP', str(response.content))

    def test_user_verify_phone_number_cache_is_None(self):
        user = UserFactory(is_phone_verified=True)
        otp_key = self._set_otp(user, '123456')
        cache.delete(otp_key)
        response = self.call_api_verify_otp('123456', otp_key)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid OTP key', str(response.content))

    def test_correct_otp(self):
        user = UserFactory(is_phone_verified=False)
        otp_key = self._set_otp(user, '123456')
        response = self.call_api_verify_otp('123456', otp_key)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_phone_verified)
        self.assertEqual(response.data['user']['id'], user.id)
        self.assertIn('token', response.data)

    def test_user_phone_number_already_verified(self):
        user = UserFactory(is_phone_verified=True)
        otp_key = self._set_otp(user, '123456')
        response = self.call_api_verify_otp('123456', otp_key)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'non_field_errors': ["User's phone number was already verified"]})
