from rest_framework import status

from artwork.factories.color_artwork import ColorArtworkFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ColorArtworkFilterApiTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.color1 = ColorArtworkFactory(category='sculpture')
        self.color2 = ColorArtworkFactory(category='painting')
        self.color3 = ColorArtworkFactory(category='painting')

    def test_filter_color_success(self):
        response = self.client.get(
            '/api/artwork/filters/color/', {
                'category': 'sculpture',
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], self.color1.category)
