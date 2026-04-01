import json
from io import BytesIO
from unittest import mock

from requests import Response
from rest_framework import status

from common.utils.hash import hash_bytes
from core.accounts.factories.user import UserFactory
from core.accounts.models import User
from core.accounts.tests.api.social_login.base_social_login_test import BaseFacebookApiTest


class FacebookLoginApiTest(BaseFacebookApiTest):

    def ignore_update_facebook_user_avatar(self):
        self.mock_task = mock.patch('core.accounts.api.social_login.facebook_login.update_facebook_user_avatar')
        self.mock_task.start()

    def test_facebook_login_create_user(self):
        self.avatar_requests.get.return_value.content = b'this is bytes'
        response = self.client.post(
            '/api/accounts/login/facebook/', {
                'access_token': 'access_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(User.objects.count(), self.user_count + 1)

        user = User.objects.latest('id')
        self.assertTrue(user.is_using_social_avatar)
        self.assertNotEqual(user.social_avatar_hash, '')

    def test_facebook_login_existing_user(self):
        user = UserFactory(is_using_social_avatar=False)
        user.socialaccount_set.create(uid=1234, provider='facebook')
        self.ignore_update_facebook_user_avatar()
        self.assertFalse(user.has_perm('accounts.can_subscribe_era_plan'))
        response = self.client.post(
            '/api/accounts/login/facebook/', {
                'access_token': 'access_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(User.objects.count(), self.user_count + 1)

        user.refresh_from_db()
        self.assertFalse(user.is_using_social_avatar)

    def test_facebook_login_not_update_avatar_if_manual_upload(self):
        user = UserFactory(is_using_social_avatar=False)
        user.socialaccount_set.create(uid=1234, provider='facebook')
        response = self.client.post(
            '/api/accounts/login/facebook/', {
                'access_token': 'access_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        user.refresh_from_db()
        self.assertEqual(user.social_avatar_hash, '')

    def test_facebook_login_not_update_avatar_if_avatar_not_changed(self):
        avatar_content = b'this is bytes'
        self.avatar_requests.get.return_value.content = avatar_content
        self._test_login_facebook_avatar_not_change(avatar_content)

    def _test_login_facebook_avatar_not_change(self, avatar_content):
        social_avatar_hash = hash_bytes(avatar_content)
        user = UserFactory(social_avatar_hash=social_avatar_hash, is_using_social_avatar=True)
        user.socialaccount_set.create(uid=1234, provider='facebook')
        response = self.client.post(
            '/api/accounts/login/facebook/', {
                'access_token': 'access_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        user.refresh_from_db()
        self.assertEqual(user.social_avatar_hash, social_avatar_hash)

    def test_facebook_login_not_update_avatar_if_avatar_failed_to_load(self):
        avatar_content = b'this is bytes'
        self.avatar_requests.get.return_value.ok = False
        self._test_login_facebook_avatar_not_change(avatar_content)

    def test_facebook_login_not_have_email(self):
        response = Response()
        response.status_code = 200
        response.raw = BytesIO(
            json.dumps({
                'id': 1234,
                'name': 'test',
            }).encode(),
        )
        self.requests.get.return_value = response
        response = self.client.post(
            '/api/accounts/login/facebook/', {
                'access_token': 'access_token',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        self.assertEqual(response.json(), {'non_field_errors': ['Email address is required for social login']})
