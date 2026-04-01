from faker import Faker
from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.collection import CollectionFactory
from artwork.factories.like_collection import LikeCollectionFactory
from artwork.factories.share_link import ShareLinkFactory
from artwork.models import Collection
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest

faker = Faker()


class CollectionApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.artwork_1 = ArtworkFactory(title='Sunset Painting', owner=self.user)
        self.artwork_2 = ArtworkFactory(title='Ocean View', owner=self.user)

        self.collection = CollectionFactory(owner=self.user, artworks=[self.artwork_1, self.artwork_2])

        self.other_user = UserFactory()

    def test_get_list_collection(self):
        CollectionFactory(artworks=[self.artwork_1, self.artwork_2])

        response = self.client.get(
            '/api/artwork/collection/',
            data={
                'owner': self.user.id,
                'artworks_page': 2,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['uuid'], str(self.collection.uuid))

    def test_get_list_collection_case_without_artwork(self):
        CollectionFactory(owner=self.user, artworks=[])

        response = self.client.get(
            '/api/artwork/collection/',
            data={
                'owner': self.user.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['image'], None)

    def test_get_collection_detail(self):
        collection = CollectionFactory(is_public=True)

        response = self.client.get(
            f'/api/artwork/collection/{collection.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(collection.uuid))
        self.assertEqual(response.data['number_of_likes'], 0)
        self.assertFalse(response.data['is_user_like'])

    def test_should_allow_owner_get_collection_private(self):
        collection = CollectionFactory(is_public=False, owner=self.user)

        response = self.client.get(
            f'/api/artwork/collection/{collection.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(collection.uuid))
        self.assertEqual(response.data['number_of_likes'], 0)
        self.assertFalse(response.data['is_user_like'])

    def test_should_not_allow_get_collection_detail_if_user_not_owner_and_collection_not_public(self):
        collection = CollectionFactory(is_public=False)

        response = self.client.get(
            f'/api/artwork/collection/{collection.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to access this collection.'})

    def test_delete_collection(self):
        collection = CollectionFactory(owner=self.user, is_public=False)

        self.assertEqual(Collection.objects.count(), 2)

        response = self.client.delete(
            f'/api/artwork/collection/{collection.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Collection.objects.count(), 1)

    def test_should_not_allow_delete_collection_if_user_is_not_owner(self):
        collection = CollectionFactory(is_public=True)

        response = self.client.delete(
            f'/api/artwork/collection/{collection.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to access this collection.'})

    def test_get_detail_collection_user_like(self):
        collection = CollectionFactory(owner=self.user)
        collection.artworks.set([])

        LikeCollectionFactory(user=self.user, collection=collection)

        response = self.client.get(
            f'/api/artwork/collection/{collection.uuid}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(collection.uuid))
        self.assertEqual(response.data['number_of_likes'], 1)
        self.assertTrue(response.data['is_user_like'])

    def test_create_collection(self):
        data = {
            'title': 'New Collection',
            'description': 'This is a new collection',
            'owner': self.user.id,
            'is_public': True,
            'artworks': [self.artwork_1.id, self.artwork_2.id],
        }
        response = self.client.post(
            '/api/artwork/collection/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Collection.objects.count(), 2)
        self.assertEqual(response.data['title'], 'New Collection')
        self.assertIn(self.artwork_1.id, response.data['artworks'])
        self.assertIn(self.artwork_2.id, response.data['artworks'])

    def test_update_collection_authenticated(self):
        new_title = 'Updated Collection Title'
        new_description = 'Updated description here.'
        data = {
            'title': new_title,
            'description': new_description,
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/artwork/collection/{self.collection.uuid}/',
            data=data,
            format='json',
        )
        self.collection.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.collection.title, new_title)
        self.assertEqual(self.collection.description, new_description)

    def test_update_collection_with_not_owner(self):
        new_title = 'Updated Collection Title'
        new_description = 'Updated description here.'
        data = {
            'title': new_title,
            'description': new_description,
        }
        user = UserFactory()
        collection = CollectionFactory(artworks=[self.artwork_2], owner=user)
        response = self.client.patch(
            f'/api/artwork/collection/{collection.uuid}/',
            data=data,
            format='json',
        )
        self.collection.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to update this collection.'})

    def test_get_list_owner_collection(self):
        CollectionFactory(artworks=[self.artwork_1, self.artwork_2], owner=self.user)
        CollectionFactory(artworks=[self.artwork_2], owner=self.user)

        response = self.client.get(
            '/api/artwork/collection/list_owner_collection/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_collection_same_artist(self):
        artist = UserFactory()
        CollectionFactory(artworks=[self.artwork_1, self.artwork_2], owner=artist)
        CollectionFactory(artworks=[self.artwork_2], owner=artist)

        response = self.client.get('/api/artwork/collection/list_collection_same_artist/',
                                   {'owner_id': artist.id},
                                   format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_collection_for_edit(self):
        collection = CollectionFactory(is_public=True)

        response = self.client.get(
            f'/api/artwork/collection/{collection.uuid}/retrieve_collection_for_edit/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(collection.uuid))
        self.assertEqual(response.data['number_of_likes'], 0)
        self.assertFalse(response.data['is_user_like'])

    def test_should_not_allow_retrieve_collection_for_edit(self):
        collection = CollectionFactory(is_public=False)

        response = self.client.get(
            f'/api/artwork/collection/{collection.uuid}/retrieve_collection_for_edit/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_gallery_collection_with_share_link(self):
        user = UserFactory()
        share_link = ShareLinkFactory(user=user, is_share_all=True, recipient_type='public')
        collection = CollectionFactory(owner=user, is_public=True)

        response = self.client.get('/api/artwork/collection/list_gallery_collection/', {
            'share_link_id': share_link.id,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['uuid'], str(collection.uuid))

    def test_get_list_gallery_collection_by_owner(self):
        response = self.client.get('/api/artwork/collection/list_gallery_collection/', {
            'user_uuid': self.user.uuid,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['uuid'], str(self.collection.uuid))

    def test_should_not_allow_get_list_gallery_collection_if_not_owner(self):
        user = UserFactory()
        self.collection.owner = user
        self.collection.save()

        response = self.client.get('/api/artwork/collection/list_gallery_collection/', {
            'user_uuid': user.uuid,
        })

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this collections.')
