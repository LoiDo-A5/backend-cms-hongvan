from rest_framework import status
from core.accounts.tests.api.base_user_test import BaseUserTest


class ChangeLanguageApiTests(BaseUserTest):
    def test_change_language_success(self):
        response = self.client.put(
            '/api/accounts/change_language/',
            data={
                'language': 'vi',
            },
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.language, 'vi')

    def test_change_language_fail_wrong_language(self):
        response = self.client.put(
            '/api/accounts/change_language/',
            data={
                'language': 'wrong_language',
            },
        )

        self.assertResponseStatus(response, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.language, 'en')
