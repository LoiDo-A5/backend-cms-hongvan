from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest


class UsablePasswordApiTests(BaseUserTest):
    def test_get_usable_password_true(self):
        self.user.set_password('x')
        self.user.save()
        response = self.client.get('/api/accounts/usable_password/')
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertTrue(response.data['has_usable_password'])

    def test_get_usable_password_false(self):
        self.user.set_unusable_password()  # called when login by social
        self.user.save()
        response = self.client.get('/api/accounts/usable_password/')
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertFalse(response.data['has_usable_password'])

    def test_user_login_via_social_then_set_password(self):
        self.test_get_usable_password_false()
        self.test_get_usable_password_true()
