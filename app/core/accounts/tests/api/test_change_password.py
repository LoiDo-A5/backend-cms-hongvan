from rest_framework import status
from core.accounts.tests.api.base_user_test import BaseUserTest


class ChangePasswordApiTests(BaseUserTest):

    def _call_api_change_password(self, old_password, new_password, confirm_password):
        response = self.client.put(
            '/api/accounts/change_password/', {
                'old_password': old_password,
                'new_password': new_password,
                'confirm_password': confirm_password,
            },
        )
        return response

    def test_change_password_success(self):
        response = self._call_api_change_password(
            old_password=self.user.raw_password,
            new_password='123',
            confirm_password='123',
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'message': 'Password updated successfully'}, response.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('123'))

    def test_change_password_fail_wrong_old_password(self):
        response = self._call_api_change_password(
            old_password='WRONG_PASSWORD',
            new_password='123',
            confirm_password='123',
        )

        self.assertResponseStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'old_password': ['Your old password is wrong']})

    def test_change_password_fail_wrong_confirm_password(self):
        response = self._call_api_change_password(
            old_password=self.user.raw_password,
            new_password='123',
            confirm_password='WRONG_CONFIRM_PASSWORD',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'non_field_errors': ['Your confirm password is wrong']})

    def test_change_password_same_as_old_password(self):
        response = self._call_api_change_password(
            old_password=self.user.raw_password,
            new_password=self.user.raw_password,
            confirm_password=self.user.raw_password,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {
            'non_field_errors': ['Your new password cannot be the same as your old password'],
        })

    def test_change_password_sets_is_first_login_false(self):
        self.user.is_first_login = True
        self.user.save(update_fields=['is_first_login'])

        response = self._call_api_change_password(
            old_password=self.user.raw_password,
            new_password='new_password123',
            confirm_password='new_password123',
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_first_login, 'is_first_login should be set to False after password change')
        self.assertTrue(self.user.check_password('new_password123'))

    def test_change_password_does_not_change_is_first_login_if_already_false(self):
        self.user.is_first_login = False
        self.user.save(update_fields=['is_first_login'])

        response = self._call_api_change_password(
            old_password=self.user.raw_password,
            new_password='another_password123',
            confirm_password='another_password123',
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_first_login, 'is_first_login should remain False')
        self.assertTrue(self.user.check_password('another_password123'))
