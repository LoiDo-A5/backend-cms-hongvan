import jwt
from rest_framework import status

from common.tests.isolated_cache_test_case import APITestCase
from core.accounts.factories.user import UserFactory


class TokenTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_refresh_token(self):
        response = self.client.post(
            '/api/accounts/token/',
            data={
                'username': self.user.username,
                'password': self.user.raw_password,
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        json = jwt.decode(
            response.data['refresh'], algorithms=['HS256'], options={
                'verify_signature': False,
            },
        )
        self.assertEqual(json['user_id'], self.user.id)
        get_refresh = self.client.post(
            '/api/accounts/token/refresh/',
            data={
                'refresh': response.data['refresh'],
            },
        )
        json = jwt.decode(
            get_refresh.data['access'], algorithms=['HS256'], options={
                'verify_signature': False,
            },
        )
        self.assertEqual(json['user_id'], self.user.id)
