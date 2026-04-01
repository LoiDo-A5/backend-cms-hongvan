from rest_framework import status

from artwork.factories.medium_artwork import MediumArtworkFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class MediumArtworkFilterApiTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.medium1 = MediumArtworkFactory(category='sculpture')
        self.medium2 = MediumArtworkFactory(category='painting')
        self.medium3 = MediumArtworkFactory(category='painting')

    def test_filter_medium_success(self):
        response = self.client.get(
            '/api/artwork/filters/medium/', {
                'category': 'sculpture',
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], self.medium1.category)
