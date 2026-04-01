from faker import Faker
from rest_framework import status

from core.accounts.factories.user import UserCollectionFactory
from core.accounts.models import UserCollection
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.factories.user import UserFactory

faker = Faker()


class CollectionApiTest(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_create_collection(self):
        response = self.client.post(
            '/api/accounts/collection/',
            data={
                'name': 'New collection',
                'is_public': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New collection')
        self.assertEqual(response.data['is_public'], True)

    def test_get_user_collection(self):
        collection_1 = UserCollectionFactory(user=self.user)
        collection_2 = UserCollectionFactory(user=self.user)
        UserCollectionFactory()

        response = self.client.get('/api/accounts/collection/', format='json')
        self.assertEqual(len(response.data), 2)

        self.assertEqual(response.data[0]['id'], collection_1.id)
        self.assertEqual(response.data[1]['id'], collection_2.id)

    def test_get_public_collection(self):
        collection = UserCollectionFactory(user=self.user, is_public=True)
        UserCollectionFactory(user=self.user, is_public=False)

        response = self.client.get('/api/accounts/collection/', format='json', data={'is_public': True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], collection.id)

    def test_get_user_view_another_user_collection(self):
        user_2 = UserFactory()

        collection = UserCollectionFactory(user=user_2, is_public=True)
        UserCollectionFactory(user=user_2, is_public=False)

        UserCollectionFactory(user=self.user, is_public=True)

        response = self.client.get(
            '/api/accounts/collection/',
            data={
                'is_public': True,
                'user_uuid': user_2.uuid,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], collection.id)

    def test_detail_collection(self):
        collection = UserCollectionFactory(user=self.user)

        response = self.client.get(f'/api/accounts/collection/{collection.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], collection.id)
        self.assertEqual(response.data['user'], collection.user.id)

    def test_update_collection(self):
        collection = UserCollectionFactory(user=self.user, name='New Collection')

        response = self.client.patch(
            f'/api/accounts/collection/{collection.id}/', {
                'name': 'collection update',
                'is_public': False,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'collection update')
        self.assertEqual(response.data['is_public'], False)

    def test_delete_publication(self):
        collection = UserCollectionFactory(user=self.user)

        response = self.client.delete(f'/api/accounts/collection/{collection.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserCollection.objects.filter(id=collection.id).exists())
