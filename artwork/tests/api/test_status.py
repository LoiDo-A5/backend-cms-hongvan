from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.api.status_can_request_certificate import EXCLUDE_STATUS


class StatusApiTest(BaseUserTest):
    def test_get_status(self):
        response = self.client.get('/api/artwork/status/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['key'], 'available')

    def test_get_status_accept_request_certificate(self):
        response = self.client.get('/api/artwork/status/can_request_certificate/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for status_item in response.data:
            self.assertNotIn(status_item['key'], EXCLUDE_STATUS)
