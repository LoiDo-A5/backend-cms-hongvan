from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest


class CategoryArtworkApiTest(BaseUserTest):
    def test_get_status(self):
        response = self.client.get('/api/artwork/category/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['key'], 'painting')
