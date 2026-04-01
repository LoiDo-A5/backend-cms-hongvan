from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


class ArtworkCountApiTest(BaseUserTest):
    def test_artwork_count(self):
        self.user.role = USER_ROLE.ARTIST
        self.user.save()
        ArtworkFactory(owner=self.user, is_public=True)
        ArtworkFactory(owner=self.user, is_public=False)

        response = self.client.get('/api/artwork/artwork_count/', {
            'owner_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 2)

    def test_artist_other_public_artwork_count(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)

        ArtworkFactory(owner=artist, is_public=True)
        ArtworkFactory(owner=artist, is_public=False)

        response = self.client.get('/api/artwork/artwork_count/', {
            'owner_uuid': artist.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 1)

    def test_collector_own_artwork_count(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        ArtworkFactory(owner=self.user, is_public=True, status='available')
        ArtworkFactory(owner=self.user, is_public=False, status='in_stock')
        ArtworkFactory(owner=self.user, status='sold')
        ArtworkFactory(owner=self.user, status='donated_gifted')

        response = self.client.get('/api/artwork/artwork_count/', {
            'owner_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 1)

    def test_collector_other_artwork_count(self):
        user = UserFactory(role=USER_ROLE.COLLECTOR)

        ArtworkFactory(owner=user, is_public=True)
        ArtworkFactory(owner=user, is_public=False)

        response = self.client.get('/api/artwork/artwork_count/', {
            'owner_uuid': user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 0)

    def test_collector_artwork_count_role_service_provider(self):
        self.user.role = USER_ROLE.SERVICE_PROVIDER
        self.user.save()

        ArtworkFactory(owner=self.user, is_public=True)
        ArtworkFactory(owner=self.user, is_public=False)

        response = self.client.get('/api/artwork/artwork_count/', {
            'owner_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 0)
