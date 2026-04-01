from rest_framework import status

from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_artist import ArtworkArtistFactory
from core.accounts.factories.user import UserFactory


class ArtistCountApiTest(BaseUserTest):
    def test_artist_count(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist1 = UserFactory(role=USER_ROLE.ARTIST)
        ArtworkFactory(owner=self.user, artist=artist1)

        artist_artwork1 = ArtworkArtistFactory(create_user=self.user)
        ArtworkFactory(owner=self.user, artist_artwork=artist_artwork1)

        ArtworkFactory(owner=self.user, artist=artist1)

        other_user = UserFactory(role=USER_ROLE.COLLECTOR)
        other_artist = UserFactory(role=USER_ROLE.ARTIST)
        ArtworkFactory(owner=other_user, artist=other_artist)

        response = self.client.get('/api/artwork/artist_count/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 2)
