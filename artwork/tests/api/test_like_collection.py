from rest_framework import status

from artwork.factories.collection import CollectionFactory
from artwork.factories.like_collection import LikeCollectionFactory
from artwork.models import LikeCollection
from common.tests.isolated_cache_test_case import APITestCase
from core.accounts.tests.api.base_user_test import BaseUserTest


class LikeCollectionApiTest(BaseUserTest):
    def test_user_like_collection(self):
        collection = CollectionFactory()

        response = self.client.post(
            f'/api/artwork/collection/{collection.uuid}/like/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'message': 'Like Success'})

        like_collection = LikeCollection.objects.first()
        self.assertEqual(like_collection.collection, collection)
        self.assertEqual(like_collection.user, self.user)

    def test_user_unlike_collection(self):
        like_collection = LikeCollectionFactory(user=self.user)
        collection = like_collection.collection

        response = self.client.post(
            f'/api/artwork/collection/{collection.uuid}/unlike/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(LikeCollection.objects.count(), 0)

    def test_get_collection_has_like_data(self):
        like_collection = LikeCollectionFactory(user=self.user)
        collection = like_collection.collection

        response = self.client.get(
            f'/api/artwork/collection/{collection.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number_of_likes'], 1)
        self.assertTrue(response.data['is_user_like'])

    def test_get_collection_not_has_like_data(self):
        collection = CollectionFactory()

        response = self.client.get(
            f'/api/artwork/collection/{collection.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['number_of_likes'], 0)
        self.assertFalse(response.data['is_user_like'])


class CollectionApiUnauthorizedTest(APITestCase):
    def test_get_collection_detail(self):
        collection = CollectionFactory()
        LikeCollectionFactory(collection=collection)

        response = self.client.get(f'/api/artwork/collection/{collection.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(collection.uuid))
        self.assertEqual(response.data['number_of_likes'], 1)
        self.assertFalse(response.data['is_user_like'])
