import threading
from unittest import mock

from django.contrib.sites.models import SITE_CACHE
from django.core.cache import cache
from django.test import TestCase as DjangoTestCase
from django.test import SimpleTestCase as DjangoSimpleTestCase
from rest_framework.test import APITestCase as RestAPITestCase


class IsolatedCacheTestMixin:
    def isolate_cache(self):
        cache.key_prefix = f'{threading.current_thread().ident}{self.id()}'

    @classmethod
    def setup_class(cls):
        cls.pusher_mocker = mock.patch('common.tasks.pusher.pusher')
        cls.mock_pusher = cls.pusher_mocker.start()
        pusher = cls.mock_pusher.Pusher.return_value
        pusher.authenticate.return_value = {
            'auth': '',
        }

    @classmethod
    def teardown_class(cls):
        cls.pusher_mocker.stop()

    def assertResponseStatus(self, response, status_code):
        self.assertEqual(response.status_code, status_code, response.content)


class TestCase(IsolatedCacheTestMixin, DjangoTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.isolate_cache()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setup_class()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.teardown_class()


class SimpleTestCase(IsolatedCacheTestMixin, DjangoSimpleTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.isolate_cache()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setup_class()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.teardown_class()


class APITestCase(IsolatedCacheTestMixin, RestAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.isolate_cache()
        SITE_CACHE.clear()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setup_class()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.teardown_class()
