from rest_framework import status

from artwork.factories.artwork_artist import ArtworkArtistFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.factories.user import UserFactory
from artwork.factories.artwork import ArtworkFactory


class FilterArtistByUserApiTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()

        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

    def test_filter_artist_by_user(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        ArtworkFactory(owner=self.user, artist=artist, artist_artwork=None)

        artist_artwork = ArtworkArtistFactory(create_user=self.user, artist_name='Tam')
        ArtworkFactory(owner=self.user, artist_artwork=artist_artwork)

        other_owner = UserFactory(role=USER_ROLE.COLLECTOR)
        other_artist = UserFactory(role=USER_ROLE.ARTIST)
        ArtworkFactory(owner=other_owner, artist=other_artist)

        other_manual_artist = ArtworkArtistFactory()
        ArtworkFactory(owner=other_owner, artist_artwork=other_manual_artist)

        response = self.client.get(
            '/api/artwork/filters/artist_by_user/', format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertIn(artist.name, response.data)
        self.assertIn(artist_artwork.artist_name, response.data)

    def test_filter_should_not_response_duplicate_artist_name(self):
        artist_artwork_1 = ArtworkArtistFactory(create_user=self.user, artist_name='Tam', year_of_birth='2000')
        ArtworkFactory(owner=self.user, artist_artwork=artist_artwork_1)

        artist_artwork_2 = ArtworkArtistFactory(create_user=self.user, artist_name='Tam', year_of_birth='2001')
        ArtworkFactory(owner=self.user, artist_artwork=artist_artwork_2)

        response = self.client.get(
            '/api/artwork/filters/artist_by_user/', format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], 'Tam')
