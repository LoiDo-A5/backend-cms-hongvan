from django.core.cache import cache
from faker import Faker
from rest_framework import status

from common.tests.isolated_cache_test_case import APITestCase
from core.accounts.factories.user import UserFactory
from core.accounts.models import User

faker = Faker()


class SocialVerifyOtpApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.user = UserFactory(phone_number=None, is_active=False)
        cls.user.socialaccount_set.create(uid=1234, provider='social')
        cls.phone = faker.phone_number()[:10]

    def test_not_request_to_verify(self):
        response = self.client.post(
            '/api/accounts/login/social/verify/', format='json',
            data={
                'phone': self.phone,
                'user': self.user.id,
                'otp': '123456',
            },
        )
        self.assertResponseStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['You have not requested to verify yet.'])

    def test_invalid_otp(self):
        user2 = UserFactory(phone_number=None)
        user2.socialaccount_set.create(uid=123456, provider='social')
        cache.set(f'{self.user.id}_social_login_otp', {'otp': '123456', 'phone': '0123456789'})
        response = self.client.post(
            '/api/accounts/login/social/verify/', format='json',
            data={
                'phone': self.phone,
                'user': self.user.id,
                'otp': '123456',
            },
        )
        self.assertResponseStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['Invalid OTP.'])
        cache.delete(f'{self.user.id}_social_login_otp')
        cache.set(f'{self.user.id}_social_login_otp', {'otp': '123456', 'phone': self.phone})
        response = self.client.post(
            '/api/accounts/login/social/verify/', format='json',
            data={
                'phone': self.phone,
                'user': self.user.id,
                'otp': '111111',
            },
        )
        self.assertEqual(response.data['non_field_errors'], ['Invalid OTP.'])

    def test_social_login_verify_success(self):
        cache.set(f'{self.user.id}_social_login_otp', {'otp': '123456', 'phone': self.phone})
        response = self.client.post(
            '/api/accounts/login/social/verify/', format='json',
            data={
                'phone': self.phone,
                'user': self.user.id,
                'otp': '123456',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, self.phone)
        self.assertTrue(self.user.is_active)

    def test_social_login_verify_success_with_exist_phone_number(self):
        exist_user = UserFactory(phone_number=self.phone)
        cache.set(f'{self.user.id}_social_login_otp', {'otp': '123456', 'phone': self.phone})
        self.assertEqual(exist_user.socialaccount_set.count(), 0)
        response = self.client.post(
            '/api/accounts/login/social/verify/', format='json',
            data={
                'phone': self.phone,
                'user': self.user.id,
                'otp': '123456',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        exist_user.refresh_from_db()
        self.assertNotEqual(exist_user.socialaccount_set.count(), 0)
        self.assertFalse(User.objects.filter(pk=self.user.id).exists())
