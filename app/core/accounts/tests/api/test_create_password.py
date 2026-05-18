from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest
from faker import Faker

faker = Faker()


class CreatePasswordApiTests(BaseUserTest):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.user.set_unusable_password()
        cls.user.save()

    def _call_api_create_password(self, new_password, confirm_password):
        response = self.client.put(
            '/api/accounts/create_password/', {
                'new_password': new_password,
                'confirm_password': confirm_password,
            },
        )
        return response

    def test_create_password_success(self):
        response = self._call_api_create_password(
            new_password='123',
            confirm_password='123',
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'message': 'Password created successfully'}, response.content)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('123'))

    def test_change_password_fail_wrong_confirm_password(self):
        response = self._call_api_create_password(
            new_password='123',
            confirm_password='WRONG_CONFIRM_PASSWORD',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'non_field_errors': ['Your confirm password is wrong']})

    def test_change_password_fail_has_usable_password(self):
        self.user.set_password(faker.name())
        self.user.save()
        response = self._call_api_create_password(
            new_password='123',
            confirm_password='123',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'message': 'Not allowed to create new password'})
