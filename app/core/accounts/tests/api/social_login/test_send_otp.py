from unittest import mock

from celery.exceptions import Retry
from django.core.cache import cache
from faker import Faker
from rest_framework import status

from common.tests.isolated_cache_test_case import APITestCase
from core.accounts.factories.user import UserFactory

faker = Faker()


class VerifyPhoneNumberApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.user = UserFactory(phone_number='')
        cls.user.socialaccount_set.create(uid=1234, provider='social')

    @mock.patch('core.accounts.api.social_login.send_otp.UserSendOtpThrottle.allow_request')
    @mock.patch('core.accounts.tasks.sms.requests')
    def test_send_sms_success(self, requests, throttle):
        requests.get.return_value.json.return_value = {
            'CodeResult': '100',
        }
        phone = faker.phone_number()[:10]
        response = self.client.post(
            '/api/accounts/login/social/send_otp/',
            data={
                'phone': phone,
                'user': self.user.id,
            },
            format='json',
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'ok')
        requests.get.assert_called_once()
        self.assertIsNotNone(cache.get(f'{self.user.id}_social_login_otp'))

    @mock.patch('core.accounts.tasks.sms.logger')
    @mock.patch('core.accounts.tasks.sms.requests')
    def test_send_sms_fail_auto_retry(self, requests, logger):
        CodeResult = 101
        requests.get.return_value.json.return_value = {
            'CodeResult': CodeResult,
        }
        phone = faker.phone_number()[:10]
        with self.assertRaises(Retry):
            self.client.post(
                '/api/accounts/login/social/send_otp/',
                data={
                    'phone': phone,
                    'user': self.user.id,
                },
                format='json',
            )
        logger.warning.assert_called_once()
        log_message = logger.warning.mock_calls[0].args[0]
        self.assertEqual(log_message, f'Fail to send sms {phone} CodeResult {CodeResult}')

    @mock.patch('core.accounts.tasks.sms.logger')
    @mock.patch('core.accounts.tasks.sms.requests')
    def test_send_sms_fail_phone_number_invalid(self, requests, logger):
        requests.get.return_value.json.return_value = {
            'CodeResult': '99',
        }
        phone = faker.phone_number()[:10]

        self.client.post(
            '/api/accounts/login/social/send_otp/',
            data={
                'phone': phone,
                'user': self.user.id,
            },
            format='json',
        )
        logger.warning.assert_called_once()
        log_message = logger.warning.mock_calls[0].args[0]
        self.assertEqual(log_message, f'Invalid phone number {phone} SMS sending failed')

    def test_send_sms_raise_validation_error(self):
        phone = faker.phone_number()[:10]
        response = self.client.post(
            '/api/accounts/login/social/send_otp/',
            data={
                'phone': phone,
                'user': UserFactory().id,
            },
            format='json',
        )
        self.assertResponseStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['user'], ['This user is not registered by social.'])
