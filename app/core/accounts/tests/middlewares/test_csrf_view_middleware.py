from unittest import mock

from django.test import SimpleTestCase

from core.accounts.middlewares import CsrfViewMiddleware


class CsrfViewMiddlewareTest(SimpleTestCase):
    def setUp(self) -> None:
        self.request = mock.MagicMock(
            csrf_processing_done=False,
            method='POST',
            _dont_enforce_csrf_checks=False,
        )
        self.get_response = mock.MagicMock()
        self.middleware = CsrfViewMiddleware(self.get_response)

    def test_ignore_none_ajax_request(self):
        self.request.META = {}
        self.middleware.process_view(self.request, None, None, None)
        self.assertFalse(self.request.csrf_processing_done)

    def test_ignore_none_origin_request(self):
        self.request.META = {
            'HTTP_ACCEPT': 'application/json',
        }
        self.middleware.process_view(self.request, None, None, None)
        self.assertFalse(self.request.csrf_processing_done)

    def test_accept_ajax_origin_request(self):
        self.request.META = {
            'HTTP_ACCEPT': 'application/json',
            'HTTP_ORIGIN': 'http://localhost',
            'HTTP_REFERER': 'http://localhost/abc',
        }
        self.middleware.process_view(self.request, None, None, None)
        self.assertTrue(self.request.csrf_processing_done)
