from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.style_artwork import StyleArtworkFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class StyleArtworkFilterApiTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.style_1 = StyleArtworkFactory(category='sculpture')
        self.style_2 = StyleArtworkFactory(category='painting')
        self.style_3 = StyleArtworkFactory(category='painting')

    def test_filter_style_by_category(self):
        response = self.client.get(
            '/api/artwork/filters/style/', {
                'category': 'sculpture',
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], self.style_1.category)

    def test_filter_style_by_user(self):
        style_4 = StyleArtworkFactory(user=self.user)

        response = self.client.get(
            '/api/artwork/filters/style/', {
                'user': self.user.id,
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], style_4.id)

    def test_default_response_is_exclude_style_has_user(self):
        StyleArtworkFactory(user=UserFactory(), category='sculpture')

        response = self.client.get(
            '/api/artwork/filters/style/', {
                'category': 'sculpture',
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], self.style_1.category)

    def test_filter_style_by_artwork_user_upload(self):
        style_4 = StyleArtworkFactory(user=UserFactory(), category='sculpture')
        ArtworkFactory(style=style_4, owner=self.user)

        response = self.client.get(
            '/api/artwork/filters/style/', {
                'category': 'sculpture',
                'by_artwork_upload': True,
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], style_4.id)
