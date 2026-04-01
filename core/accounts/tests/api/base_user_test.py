from rest_framework.authtoken.models import Token

from common.tests.isolated_cache_test_case import APITestCase
from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.user import UserFactory
from core.accounts.models import User


class BaseUserMixinTest:
    @classmethod
    def _create_user(cls):
        user = UserFactory()
        return user

    def _setup_credentials(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    @classmethod
    def setup_user(cls):
        cls.user: User = cls._create_user()
        cls.token = Token.objects.create(user=cls.user)


class BaseUserTest(BaseUserMixinTest, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.setup_user()

    def setUp(self) -> None:
        super().setUp()
        self._setup_credentials()


class BaseUserSubscribeTest(BaseUserTest):
    pass


class BaseAdminTest(BaseUserMixinTest, TestCase):
    @classmethod
    def _create_user(cls):
        return UserFactory(is_superuser=True, is_staff=True)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user: User = cls._create_user()

    def setUp(self) -> None:
        super().setUp()
        self.client.force_login(self.user)
