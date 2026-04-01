from rest_framework import status

from artwork.factories.exhibition import ExhibitionFactory
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


class ExhibitionCountApiTest(BaseUserTest):
    def test_exhibition_count(self):
        ExhibitionFactory(owner=self.user, is_public=True)
        ExhibitionFactory(owner=self.user, is_public=False)

        response = self.client.get('/api/artwork/exhibition_count/', {
            'owner_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 2)

    def test_artist_other_public_artwork_count(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)

        ExhibitionFactory(owner=artist, is_public=True)
        ExhibitionFactory(owner=artist, is_public=False)

        response = self.client.get('/api/artwork/exhibition_count/', {
            'owner_uuid': artist.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 1)
