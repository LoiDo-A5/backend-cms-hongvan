from rest_framework import status

from common.utils.hash import hash_bytes
from core.accounts.factories.user import UserFactory
from core.accounts.models import User
from core.accounts.tests.api.social_login.base_social_login_test import BaseGoogleApiTest


class GoogleLoginApiTests(BaseGoogleApiTest):

    def _setup_existed_user(self):
        user = UserFactory(is_using_social_avatar=False)
        user.socialaccount_set.create(uid=f'{self.app.id}-1234', provider='custom_google')
        self.avatar_requests.get.return_value.content = b'this is bytes'
        return user

    def test_google_login_create_user(self):
        self.avatar_requests.get.return_value.content = b'this is bytes'
        response = self.client.post(
            '/api/accounts/login/google/', {
                'access_token': 'google_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.count(), self.user_count + 1)

        user = User.objects.latest('id')
        self.assertEqual(user.name, 'EoH')
        self.assertTrue(user.is_using_social_avatar)
        self.assertNotEqual(user.social_avatar_hash, '')

        self.assertEqual(user.socialaccount_set.filter(provider='custom_google').count(), 1)
        social_account = user.socialaccount_set.filter(provider='custom_google').get()
        self.assertEqual(social_account.uid, f'{self.app.id}-1234')

    def test_google_login_create_user_but_no_allow_internal_testing(self):
        self.avatar_requests.get.return_value.content = b'this is bytes'
        response = self.client.post(
            '/api/accounts/login/google/', {
                'access_token': 'google_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_google_login_existing_user(self):
        user = self._setup_existed_user()
        response = self.client.post(
            '/api/accounts/login/google/', {
                'access_token': 'google_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(User.objects.count(), self.user_count + 1)
        user.refresh_from_db()
        self.assertFalse(user.is_using_social_avatar)

    def test_google_login_not_update_avatar_if_manual_upload(self):
        user = self._setup_existed_user()
        response = self.client.post(
            '/api/accounts/login/google/', {
                'access_token': 'google_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        user.refresh_from_db()
        self.assertEqual(user.social_avatar_hash, '')
        self.assertFalse(user.is_using_social_avatar)

    def _test_login_not_change_avatar(self, avatar_content):
        social_avatar_hash = hash_bytes(avatar_content)
        user = UserFactory(social_avatar_hash=social_avatar_hash, is_using_social_avatar=True)
        user.socialaccount_set.create(uid=f'{self.app.id}-1234', provider='custom_google')
        response = self.client.post(
            '/api/accounts/login/google/', {
                'access_token': 'google_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        user.refresh_from_db()
        self.assertEqual(user.social_avatar_hash, social_avatar_hash)

    def test_google_login_not_update_avatar_if_avatar_not_changed(self):
        avatar_content = b'this is bytes'
        self.avatar_requests.get.return_value.content = avatar_content
        self._test_login_not_change_avatar(avatar_content)

    def test_google_login_not_update_avatar_if_avatar_failed_to_load(self):
        avatar_content = b'this is bytes'
        self.avatar_requests.get.return_value.ok = False
        self._test_login_not_change_avatar(avatar_content)
