from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.like_artwork import LikeArtworkFactory
from artwork.models import LikeArtwork
from common.tests.isolated_cache_test_case import APITestCase
from core.accounts.tests.api.base_user_test import BaseUserTest


class LikeArtworkApiTest(BaseUserTest):
    def test_user_like_artwork(self):
        artwork = ArtworkFactory()

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.uuid}/like/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'message': 'Like Success'})

        like_artwork = LikeArtwork.objects.first()
        self.assertEqual(like_artwork.artwork, artwork)
        self.assertEqual(like_artwork.user, self.user)

    def test_user_unlike_artwork(self):
        like_artwork = LikeArtworkFactory(user=self.user)
        artwork = like_artwork.artwork

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.uuid}/unlike/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LikeArtwork.objects.count(), 0)

    def test_get_artwork_has_like_data(self):
        like_artwork = LikeArtworkFactory(user=self.user)
        artwork = like_artwork.artwork

        response = self.client.get(
            f'/api/artwork/artwork/{artwork.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number_of_likes'], 1)
        self.assertTrue(response.data['is_user_like'])

    def test_get_artwork_not_has_like_data(self):
        artwork = ArtworkFactory()

        response = self.client.get(
            f'/api/artwork/artwork/{artwork.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number_of_likes'], 0)
        self.assertFalse(response.data['is_user_like'])


class ArtworkApiUnauthorizedTest(APITestCase):
    def test_get_artwork_detail(self):
        artwork = ArtworkFactory(status='available')
        LikeArtworkFactory(artwork=artwork)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], artwork.id)
        self.assertEqual(response.data['number_of_likes'], 1)
        self.assertFalse(response.data['is_user_like'])

    def test_get_artwork_detail_by_view_user(self):
        artwork = ArtworkFactory(status='available')
        LikeArtworkFactory(artwork=artwork)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/artwork_view_info/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], artwork.id)
        self.assertEqual(response.data['number_of_likes'], 1)
        self.assertFalse(response.data['is_user_like'])
