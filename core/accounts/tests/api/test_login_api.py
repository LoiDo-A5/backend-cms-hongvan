from io import StringIO
from django.core.files import File
from rest_framework import status
from rest_framework.authtoken.models import Token

from common.tests.isolated_cache_test_case import APITestCase
from core.accounts.factories.user import UserFactory


class UserAuthTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_user_login_default_eoh(self):
        response = self.client.post(
            '/api/accounts/login/', {
                'username': self.user.username,
                'password': self.user.raw_password,
            },
        )

        self.assert_login_success(response)

    def test_user_avatar_must_have_response_with_http(self):
        file_content = StringIO()
        avatar = File(file_content, 'mock-file')
        self.user.avatar = avatar
        self.user.save()

        response = self.client.post(
            '/api/accounts/login/', {
                'username': self.user.username,
                'password': self.user.raw_password,
            },
        )
        self.assertIn('http://testserver', response.data['user']['avatar'])

    def assert_login_success(self, response):
        self.assertResponseStatus(response, status.HTTP_200_OK)
        token = Token.objects.get(user=self.user)
        self.assertEqual(response.data['token'], token.key)
        self.assertEqual(response.data['user']['name'], self.user.name)
        self.assertEqual(response.data['user']['has_activated'], True)

    def test_incorrect_user_login(self):
        response = self.client.post(
            '/api/accounts/login/', {
                'username': self.user.username,
                'password': self.user.password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_not_has_activated_login(self):
        self.user.has_activated = False
        self.user.save()
        response = self.client.post(
            '/api/accounts/login/', {
                'username': self.user.username,
                'password': self.user.raw_password,
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['has_activated'], True)

    def test_user_has_activated_login(self):
        self.user.has_activated = True
        self.user.save()
        response = self.client.post(
            '/api/accounts/login/', {
                'username': self.user.username,
                'password': self.user.raw_password,
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['has_activated'], True)

    def test_user_logout_api(self):
        response = self.client.post('/api/accounts/logout/')
        # todo Bang: assert more
        self.assertEqual(response.status_code, status.HTTP_200_OK)
