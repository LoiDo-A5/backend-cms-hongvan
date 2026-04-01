import os
from unittest import skipIf

from rest_framework import status

from common.tests.isolated_cache_test_case import TestCase


class SwaggerDocumentTest(TestCase):
    @skipIf(
        not os.getenv('TEST_API'),
        reason='This is for local testing if api document is ok, skip coverage on CI',
    )
    def test_get_api_doc(self):  # pragma: nocover
        response = self.client.get('/swagger/?format=openapi')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
