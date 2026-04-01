from artwork.factories.artwork import ArtworkFactory
from artwork.factories.exhibition import ExhibitionFactory
from artwork.factories.exhibition_group import ExhibitionGroupFactory
from artwork.models import Exhibition, ExhibitionGroup
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest
from rest_framework import status


class ExhibitionApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.ARTIST
        self.user.save()

    def test_create_exhibition(self):
        artwork = ArtworkFactory(owner=self.user)
        artwork_2 = ArtworkFactory(owner=self.user)

        data = {
            'title': 'Art Exhibition',
            'date_start': '2025-01-01T10:00:00Z',
            'date_end': '2025-01-10T18:00:00Z',
            'address': '123 Art Street',
            'event_type': 'free_ticket',
            'preface': 'An amazing art exhibition.',
            'groups': [
                {
                    'title': 'Group 1',
                    'description': 'Description group 1',
                    'artworks': [artwork.id, artwork_2.id],
                },
                {
                    'title': 'Group 2',
                    'description': 'Description group 2',
                    'artworks': [artwork.id, artwork_2.id],
                },
            ],
        }

        response = self.client.post(
            '/api/artwork/exhibition/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Exhibition.objects.count(), 1)

        exhibition = Exhibition.objects.first()
        self.assertEqual(exhibition.title, data['title'])
        self.assertEqual(exhibition.address, data['address'])
        self.assertEqual(exhibition.event_type, data['event_type'])
        self.assertEqual(exhibition.preface, data['preface'])
        self.assertEqual(exhibition.owner, self.user)

        self.assertEqual(ExhibitionGroup.objects.count(), 2)
        exhibition_group_1 = ExhibitionGroup.objects.get(title='Group 1')
        self.assertEqual(exhibition_group_1.exhibition, exhibition)

    def test_get_list_exhibition_user_is_owner(self):
        ExhibitionFactory(owner=self.user)
        ExhibitionFactory(is_public=False, owner=self.user)
        ExhibitionFactory(is_draft=False, owner=self.user)
        ExhibitionFactory()

        response = self.client.get('/api/artwork/exhibition/', {
            'user_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results']
        self.assertEqual(len(data), 3)

    def test_get_list_exhibition_user_is_not_owner(self):
        user = UserFactory()
        exhibition = ExhibitionFactory(owner=user, is_public=True, is_draft=False)
        ExhibitionFactory(owner=user, is_public=False, is_draft=False)
        ExhibitionFactory(owner=user, is_public=True, is_draft=True)

        response = self.client.get('/api/artwork/exhibition/', {
            'user_uuid': user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], exhibition.id)

    def test_save_as_draft_exhibition(self):
        data = {
            'title': 'Art Exhibition',
            'date_start': '2025-01-01T10:00:00Z',
            'date_end': '2025-01-10T18:00:00Z',
            'address': '123 Art Street',
            'event_type': 'free_ticket',
            'preface': 'An amazing art exhibition.',
        }

        response = self.client.post(
            '/api/artwork/exhibition/save_as_draft/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Exhibition.objects.count(), 1)

        exhibition = Exhibition.objects.first()
        self.assertEqual(exhibition.title, data['title'])
        self.assertEqual(exhibition.address, data['address'])
        self.assertEqual(exhibition.event_type, data['event_type'])
        self.assertEqual(exhibition.preface, data['preface'])
        self.assertEqual(exhibition.owner, self.user)

    def test_update_exhibition_without_groups(self):
        exhibition = ExhibitionFactory(owner=self.user)

        date_start = '2025-01-05T10:00:00+00:00'
        date_end = '2025-01-15T18:00:00+00:00'

        data = {
            'title': 'Updated Art Exhibition',
            'date_start': date_start,
            'date_end': date_end,
            'address': '456 Art Avenue',
            'preface': 'An updated art exhibition.',
            'is_public': False,
            'event_type': 'free_ticket',
        }

        response = self.client.patch(
            f'/api/artwork/exhibition/{exhibition.id}/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        exhibition.refresh_from_db()
        self.assertEqual(exhibition.title, data['title'])
        self.assertEqual(exhibition.date_start.isoformat(), date_start)
        self.assertEqual(exhibition.date_end.isoformat(), date_end)
        self.assertEqual(exhibition.address, data['address'])
        self.assertEqual(exhibition.event_type, data['event_type'])
        self.assertEqual(exhibition.preface, data['preface'])
        self.assertFalse(exhibition.is_public)

    def test_update_exhibition_with_new_group(self):
        exhibition = ExhibitionFactory(owner=self.user)
        artwork_1 = ArtworkFactory(owner=self.user)
        artwork_2 = ArtworkFactory(owner=self.user)

        data = {
            'title': 'Updated Art Exhibition with New Group',
            'date_start': '2025-01-05T10:00:00Z',
            'date_end': '2025-01-15T18:00:00Z',
            'address': '456 Art Avenue',
            'event_type': 'free_ticket',
            'preface': 'An updated exhibition with a new group.',
            'is_public': True,
            'groups': [
                {
                    'title': 'New Group',
                    'description': 'New description for the group.',
                    'artworks': [artwork_1.id, artwork_2.id],
                },
            ],
        }

        response = self.client.patch(
            f'/api/artwork/exhibition/{exhibition.id}/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        exhibition.refresh_from_db()
        self.assertEqual(exhibition.title, data['title'])
        exhibition_group = ExhibitionGroup.objects.get(title='New Group')
        self.assertEqual(exhibition_group.exhibition, exhibition)

    def test_update_exhibition_with_removed_group(self):
        exhibition = ExhibitionFactory(owner=self.user)
        group_to_remove = ExhibitionGroupFactory(exhibition=exhibition)
        artwork_1 = ArtworkFactory(owner=self.user)

        data = {
            'title': 'Updated Exhibition without Group',
            'date_start': '2025-01-05T10:00:00Z',
            'date_end': '2025-01-15T18:00:00Z',
            'address': '456 Art Avenue',
            'event_type': 'free_ticket',
            'preface': 'An updated exhibition without one of the groups.',
            'is_public': True,
            'groups': [
                {
                    'title': 'Updated Group',
                    'description': 'Updated description for the group.',
                    'artworks': [artwork_1.id],
                },
            ],
        }

        response = self.client.patch(
            f'/api/artwork/exhibition/{exhibition.id}/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, 200)

        exhibition.refresh_from_db()

        with self.assertRaises(ExhibitionGroup.DoesNotExist):
            ExhibitionGroup.objects.get(id=group_to_remove.id)

        updated_group = ExhibitionGroup.objects.get(title='Updated Group')
        self.assertEqual(updated_group.exhibition, exhibition)
        self.assertEqual(list(updated_group.artworks.all()), [artwork_1])

    def test_create_new_exhibition_group_on_update(self):
        exhibition = ExhibitionFactory(owner=self.user)

        new_group_data = {
            'title': 'New Group',
            'description': 'A newly added group',
            'artworks': [],
        }

        update_data = {
            'groups': [new_group_data],
        }

        response = self.client.patch(
            f'/api/artwork/exhibition/{exhibition.id}/',
            data=update_data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        exhibition.refresh_from_db()
        groups = exhibition.groups.all()
        self.assertEqual(groups.count(), 1)
        self.assertEqual(groups[0].title, new_group_data['title'])
        self.assertEqual(groups[0].description, new_group_data['description'])
        self.assertEqual(groups[0].exhibition, exhibition)

    def test_update_exhibition_without_group_removal(self):
        exhibition = ExhibitionFactory(owner=self.user)
        existing_group = ExhibitionGroupFactory(exhibition=exhibition)

        artwork_1 = ArtworkFactory(owner=self.user)
        data = {
            'title': 'Updated Exhibition with Same Groups',
            'date_start': '2025-01-05T10:00:00Z',
            'date_end': '2025-01-15T18:00:00Z',
            'address': '456 Art Avenue',
            'event_type': 'free_ticket',
            'preface': 'Updated exhibition without changing existing groups.',
            'is_public': True,
            'groups': [
                {
                    'id': existing_group.id,
                    'title': existing_group.title,
                    'description': existing_group.description,
                    'artworks': [artwork_1.id],
                },
            ],
        }

        response = self.client.patch(
            f'/api/artwork/exhibition/{exhibition.id}/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, 200)

    def test_update_exhibition_with_missing_artworks_in_group(self):
        exhibition = ExhibitionFactory(owner=self.user)
        group_to_update = ExhibitionGroupFactory(exhibition=exhibition)

        data = {
            'title': 'Updated Exhibition with Invalid Group Data',
            'date_start': '2025-01-05T10:00:00Z',
            'date_end': '2025-01-15T18:00:00Z',
            'address': '456 Art Avenue',
            'event_type': 'free_ticket',
            'preface': 'This should fail due to missing artworks in the group.',
            'is_public': True,
            'groups': [
                {
                    'id': group_to_update.id,
                    'title': 'Updated Group Without Artworks',
                    'description': 'This group has no artworks.',
                    'artworks': [],
                },
            ],
        }

        response = self.client.patch(
            f'/api/artwork/exhibition/{exhibition.id}/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, 200)

    def test_delete_exhibition(self):
        exhibition = ExhibitionFactory(owner=self.user)

        response = self.client.delete(f'/api/artwork/exhibition/{exhibition.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_exhibition_not_owner(self):
        exhibition = ExhibitionFactory()

        response = self.client.delete(f'/api/artwork/exhibition/{exhibition.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to delete this exhibition.'})

    def test_get_exhibition_detail(self):
        exhibition = ExhibitionFactory(owner=self.user)
        existing_group = ExhibitionGroupFactory(exhibition=exhibition)

        response = self.client.get(
            f'/api/artwork/exhibition/{exhibition.id}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], exhibition.id)
        self.assertEqual(response.data['title'], exhibition.title)
        self.assertIn('groups', response.data)
        groups = response.data['groups']
        self.assertEqual(len(groups), 1)
        group_data = groups[0]
        self.assertEqual(group_data['id'], existing_group.id)
        self.assertEqual(group_data['title'], existing_group.title)

    def test_get_exhibition_detail_not_public_and_not_owner(self):
        exhibition = ExhibitionFactory(is_public=False)

        response = self.client.get(
            f'/api/artwork/exhibition/{exhibition.id}/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to access this exhibition.'})

    def test_update_exhibition_with_not_owner(self):
        exhibition = ExhibitionFactory()

        data = {
            'title': 'Updated Art Exhibition',
            'event_type': 'free_ticket',
        }

        response = self.client.patch(
            f'/api/artwork/exhibition/{exhibition.id}/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to edit this exhibition.'})

    def test_exhibition_get_list_artist_name(self):
        exhibition = ExhibitionFactory(owner=self.user)
        artwork = ArtworkFactory(owner=self.user)
        artist_name = artwork.artist_artwork

        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork_2 = ArtworkFactory(artist_artwork=None, owner=self.user, artist=artist)

        ExhibitionGroupFactory(exhibition=exhibition, artworks=[artwork])
        ExhibitionGroupFactory(exhibition=exhibition, artworks=[artwork_2])

        response = self.client.get(
            f'/api/artwork/exhibition/{exhibition.id}/list_artist_name/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['artist_name'], artist_name.artist_name)
        self.assertEqual(results[0]['artwork_count'], 1)

        self.assertEqual(results[1]['artist_name'], artist.name)
        self.assertEqual(results[1]['artwork_count'], 1)
