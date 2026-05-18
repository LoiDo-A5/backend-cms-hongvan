from rest_framework import status

from core.accounts.factories.allauth import SocialAppFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class SocialAccountApiTests(BaseUserTest):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        SocialAppFactory(sites=[1], provider='google')
        SocialAppFactory(sites=[1], provider='facebook')
        cls.user.socialaccount_set.create(provider='google', uid='123')
        cls.user.socialaccount_set.create(provider='facebook', uid='456')

    def test_get_social_accounts(self):
        response = self.client.get('/api/accounts/social_accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_disconnect_social_account_success(self):
        self.assertEqual(self.user.socialaccount_set.count(), 2)
        response = self.client.post(
            f'/api/accounts/social_accounts/{self.user.socialaccount_set.first().id}/disconnect/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.socialaccount_set.count(), 1)

    def test_disconnect_all_social_account_password_and_phone_number_set_up(self):
        self.user.socialaccount_set.first().delete()
        self.assertEqual(self.user.socialaccount_set.count(), 1)
        response = self.client.post(
            f'/api/accounts/social_accounts/{self.user.socialaccount_set.first().id}/disconnect/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.socialaccount_set.count(), 0)

    def test_disconnect_all_social_account_password_not_set_up(self):
        self.user.socialaccount_set.first().delete()
        self.assertEqual(self.user.socialaccount_set.count(), 1)
        self.user.set_unusable_password()
        self.user.save()
        response = self.client.post(
            f'/api/accounts/social_accounts/{self.user.socialaccount_set.first().id}/disconnect/',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'detail': 'Your account must be set up password and phone number'})

    def test_disconnect_all_social_account_phone_number_not_set_up(self):
        self.user.socialaccount_set.first().delete()
        self.assertEqual(self.user.socialaccount_set.count(), 1)
        self.user.phone_number = None
        self.user.is_phone_verified = False
        self.user.save()
        response = self.client.post(
            f'/api/accounts/social_accounts/{self.user.socialaccount_set.first().id}/disconnect/',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'detail': 'Your account must be set up password and phone number'})
