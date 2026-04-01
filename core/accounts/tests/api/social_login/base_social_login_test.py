import json
from io import BytesIO
from unittest import mock

from django.conf import settings
from requests import Response

from common.tests.isolated_cache_test_case import APITestCase
from core.accounts.factories.allauth import SocialAppFactory
from core.accounts.models import User


class BaseGoogleApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.app = SocialAppFactory(sites=[settings.SITE_ID], provider='custom_google')

    def setUp(self) -> None:
        super().setUp()
        self.gg_requests_mock = mock.patch('allauth.socialaccount.providers.google.views.requests')
        requests = self.gg_requests_mock.start()
        self.avatar_requests_mock = mock.patch('core.accounts.api.social_login.google_login.requests')
        self.avatar_requests = self.avatar_requests_mock.start()

        response = Response()
        response.status_code = 200
        response.raw = BytesIO(
            json.dumps({
                'id': 1234,
                'picture': 'https://google.com/',
                'name': 'EoH',
                'email': 'email@eoh.io',
            }).encode(),
        )
        requests.get.return_value = response  # google response
        self.user_count = User.objects.count()

    def tearDown(self) -> None:
        super().tearDown()
        self.gg_requests_mock.stop()
        self.avatar_requests_mock.stop()


class BaseFacebookApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        SocialAppFactory(sites=[settings.SITE_ID], provider='facebook')

    def setUp(self) -> None:
        super().setUp()
        self.fb_requests_mock = mock.patch('allauth.socialaccount.providers.facebook.views.requests')
        self.avatar_requests_mock = mock.patch('core.accounts.tasks.user_avatar.requests')

        self.avatar_requests = self.avatar_requests_mock.start()
        self.requests = self.fb_requests_mock.start()

        response = Response()
        response.status_code = 200
        response.raw = BytesIO(
            json.dumps({
                'id': 1234,
                'name': 'test',
                'email': 'email@eoh.io',
            }).encode(),
        )

        self.requests.get.return_value = response  # facebook response
        self.user_count = User.objects.count()
        self.mock_task = None

    def tearDown(self) -> None:
        super().tearDown()
        self.fb_requests_mock.stop()
        self.avatar_requests_mock.stop()
        if self.mock_task:
            self.mock_task.stop()
