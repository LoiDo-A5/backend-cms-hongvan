from rest_framework import status

from artwork.factories.orientation_artwork import OrientationArtworkFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class OrientationArtworkFilterApiTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()

        self.orientation1 = OrientationArtworkFactory(category='sculpture')
        self.orientation2 = OrientationArtworkFactory(category='painting')
        self.orientation3 = OrientationArtworkFactory(category='painting')

    def test_filter_orientation_success(self):
        response = self.client.get(
            '/api/artwork/filters/orientation/', {
                'category': 'sculpture',
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], self.orientation1.category)
