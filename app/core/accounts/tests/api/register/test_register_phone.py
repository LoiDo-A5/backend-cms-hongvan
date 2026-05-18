import requests_mock
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status

from common.tests.isolated_cache_test_case import APITestCase
from common.tests.isolated_cache_test_case import SimpleTestCase
from core.accounts.factories.user import UserFactory
from core.accounts.models import User
import requests


class LoginAssignTestingPlanMixin(SimpleTestCase):
    def setUp(self):
        super().setUp()


@requests_mock.Mocker()
class RegisterPhoneTests(APITestCase, LoginAssignTestingPlanMixin):
    def send_register(self, data, **extra):
        response = self.client.post(
            '/api/accounts/register/phone/', data,
            **extra,
        )
        return response

    def mock_sms(self, m):
        m.register_uri(
            'GET', 'http://rest.esms.vn/MainService.svc/json/SendMultipleMessage_V4_get', json={
                'CodeResult': '100',
            },
        )

    def mock_sendbird(self, m):
        m.register_uri(
            'POST', f'{settings.SENDBIRD_API_URL}/users',
            json={
                'user_id': '12345',
                'nickname': 'John Doe',
                'profile_url': None,
            },
        )

    def test_register_phone_not_timezone_and_timezone_null(self, m):
        self.mock_sms(m)
        self.mock_sendbird(m)
        data = {
            'phone': '0901234567',
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
        }
        response = self.send_register(data)
        self.assertResponseStatus(response, status.HTTP_200_OK)

        data = {
            'phone': '0900000001',
            'email': 'e0001@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': '',
        }
        response = self.send_register(data)
        self.assertResponseStatus(response, status.HTTP_200_OK)
        user = User.objects.get(phone_number='0900000001')
        self.assertEqual(user.time_zone, 'Asia/Ho_Chi_Minh')

    @override_settings(IS_TEST=False, THROTTLE_RATES_USER_REGISTER='1/s')
    def test_throttle_send_opt_register_phone(self, m):
        self.mock_sms(m)
        self.mock_sendbird(m)
        data = {
            'phone': '0901234567',
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.send_register(data)
        self.assertResponseStatus(response, status.HTTP_200_OK)

        # again
        response = self.send_register(data)
        self.assertResponseStatus(response, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_password_not_match(self, m):
        data = {
            'phone': '0901234567',
            'email': 'email@gmail.com',
            'password1': 'jfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.send_register(data).json()
        self.assertEqual(response['non_field_errors'], ["The two password fields didn't match."])

    def test_register_with_existed_phone_number(self, m):
        m.register_uri(
            'GET', 'http://rest.esms.vn/MainService.svc/json/SendMultipleMessage_V4_get', json={
                'CodeResult': '100',
            },
        )

        user = UserFactory(
            phone_number='0901234567',

        )
        data = {
            'phone': user.phone_number,
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.send_register(data)
        self.assertResponseStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['non_field_errors'], [
                "There's an account associated with this phone number. "
                "If that's yours, please go back to Forgot password to set a new one.",
            ],
        )

    def test_register_with_existed_phone_number_but_not_verified(self, m):
        self.mock_sms(m)
        self.mock_sendbird(m)
        user = UserFactory(
            is_phone_verified=False,

        )
        data = {
            'phone': user.phone_number,
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.send_register(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()['phone']
        self.assertEqual(data['code'], 'phone_need_verify')
        self.assertEqual(data['user_id'], str(user.id))
        self.assertEqual(data['message'], 'The phone number is registered but not verified. Please verify phone number')
        self.assertEqual(data['phone'], user.phone_number)
        self.assertEqual(data['key'], str(user.register_otp_key))

    def test_register_with_existed_email(self, m):
        existing = UserFactory()
        data = {
            'phone': '0901234567',
            'email': existing.email,
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.send_register(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'], ['Email address already in use'])

    def test_register_with_non_digit_phone_number(self, m):
        existing = UserFactory()
        data = {
            'phone': 'a0901234567',
            'email': existing.email,
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.send_register(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['phone'], ['Phone number must only contain digits'])

    def test_register_phone_success(self, m):
        self.mock_sms(m)
        self.mock_sendbird(m)
        data = {
            'phone': '0901234567',
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.send_register(data)
        user = User.objects.get(phone_number='0901234567')
        self.assertFalse(user.is_phone_verified)
        self.assertTrue(user.is_active)
        self.assertIsNotNone(cache.get(user.register_otp_key))
        self.assertEqual(response.data['message'], 'Sent OTP code')
        self.assertIsNone(user.referred_by)

    def test_register_success_but_no_allow_internal_testing(self, m):
        self.mock_sms(m)
        self.mock_sendbird(m)
        data = {
            'phone': '0901234567',
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }
        response = self.send_register(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register_phone_success_with_existed_referral_code(self, m):
        user = UserFactory()
        self.mock_sms(m)
        self.mock_sendbird(m)
        data = {
            'phone': '0901234567',
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
            'referred_by': user.referral_code,
        }
        response = self.send_register(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_user = User.objects.get(phone_number='0901234567')
        self.assertEqual(new_user.referred_by, user)

    def test_register_phone_fail_with_non_existed_referral_code(self, m):
        self.mock_sms(m)
        self.mock_sendbird(m)
        data = {
            'phone': '0901234567',
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
            'referred_by': 'ABCDEF',
        }
        response = self.send_register(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['referred_by'], ['Invalid referral code, please check again.'])

    def test_register_phone_success_with_referral_code_empty(self, m):
        self.mock_sms(m)
        self.mock_sendbird(m)
        data = {
            'phone': '0901234567',
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
            'referred_by': '',
        }
        response = self.send_register(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_user = User.objects.get(phone_number='0901234567')
        self.assertIsNone(new_user.referred_by)

    def test_register_phone_sendbird_request_exception(self, m):
        self.mock_sms(m)
        m.register_uri(
            'POST',
            f'{settings.SENDBIRD_API_URL}/users',
            exc=requests.exceptions.RequestException('Sendbird API error'),
        )

        data = {
            'phone': '0901234567',
            'email': 'email@gmail.com',
            'password1': 'jkasdfbj',
            'password2': 'jkasdfbj',
            'time_zone': 'Asia/Jakarta',
        }

        response = self.send_register(data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['sendbird'],
            'Failed to create Sendbird user. Please try again later.',
        )
