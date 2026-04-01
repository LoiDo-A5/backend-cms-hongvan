from rest_framework import status

from artwork.factories.collection import CollectionFactory
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


class CollectionCountApiTest(BaseUserTest):
    def test_artist_own_collection_count(self):
        self.user.role = USER_ROLE.ARTIST
        self.user.save()

        CollectionFactory(owner=self.user, is_public=True)
        CollectionFactory(owner=self.user, is_public=False)

        response = self.client.get('/api/artwork/collection_count/', {
            'owner_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 2)

    def test_artist_other_public_collection_count(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)

        CollectionFactory(owner=artist, is_public=True)
        CollectionFactory(owner=artist, is_public=False)

        response = self.client.get('/api/artwork/collection_count/', {
            'owner_uuid': artist.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 1)

    def test_collector_own_collection_count(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        CollectionFactory(owner=self.user, is_public=True)
        CollectionFactory(owner=self.user, is_public=False)

        response = self.client.get('/api/artwork/collection_count/', {
            'owner_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 2)

    def test_collector_other_collection_count(self):
        collector = UserFactory(role=USER_ROLE.COLLECTOR)

        CollectionFactory(owner=collector, is_public=True)
        CollectionFactory(owner=collector, is_public=False)

        response = self.client.get('/api/artwork/collection_count/', {
            'owner_uuid': collector.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 0)

    def test_service_provider_collection_count(self):
        service_provider = UserFactory(role=USER_ROLE.SERVICE_PROVIDER)

        CollectionFactory(owner=service_provider, is_public=True)
        CollectionFactory(owner=service_provider, is_public=False)

        response = self.client.get('/api/artwork/collection_count/', {
            'owner_uuid': service_provider.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 0)
