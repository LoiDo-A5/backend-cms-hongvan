from rest_framework import status

from artwork.factories.artist_tag_request import ArtistTagRequestFactory
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_artist import ArtworkArtistFactory
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


class UserArtistApiTest(BaseUserTest):
    def test_get_user_artist_by_uuid(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist = UserFactory(role=USER_ROLE.ARTIST, legal_name='John')

        artwork_1 = ArtworkFactory(owner=self.user)
        ArtistTagRequestFactory(artwork=artwork_1, request_by=self.user, request_to=artist)

        response = self.client.get(f'/api/artwork/user/artist/{artist.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(artist.uuid))
        self.assertEqual(response.data['legal_name'], artist.legal_name)

    def test_get_user_artist_by_uuid_by_string(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist = UserFactory(role=USER_ROLE.ARTIST, legal_name='John', uuid='johny')

        artwork_1 = ArtworkFactory(owner=self.user)
        ArtistTagRequestFactory(artwork=artwork_1, request_by=self.user, request_to=artist)

        response = self.client.get(f'/api/artwork/user/artist/{artist.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], str(artist.uuid))
        self.assertEqual(response.data['legal_name'], artist.legal_name)

    def test_get_user_artist_by_artist_artwork_id(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artist = ArtworkArtistFactory()
        ArtworkFactory(owner=self.user, artist_artwork=artist)

        response = self.client.get(
            f'/api/artwork/user/artist/{artist.id}/',
            format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['artist_name'], artist.artist_name)

    def test_update_artist(self):
        artist = ArtworkArtistFactory(create_user=self.user)

        response = self.client.patch(
            f'/api/artwork/user/artist/{artist.id}/',
            data={
                'artist_name': 'John',
                'contact_info': '09xx',
                'year_of_birth': '2000',
                'year_of_death': '2080',
            },
            format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        artist.refresh_from_db()
        self.assertEqual(artist.artist_name, 'John')
        self.assertEqual(artist.contact_info, '09xx')
        self.assertEqual(artist.year_of_birth, '2000')
        self.assertEqual(artist.year_of_death, '2080')

    def test_should_allow_update_artist_with_exist_current_data(self):
        artist = ArtworkArtistFactory(create_user=self.user)

        response = self.client.patch(
            f'/api/artwork/user/artist/{artist.id}/',
            data={
                'artist_name': artist.artist_name,
                'year_of_birth': artist.year_of_birth,
            },
            format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_should_not_allow_update_duplicate_data_exist_artist(self):
        artist = ArtworkArtistFactory(artist_name='John', year_of_birth='2000', create_user=self.user)
        artist_2 = ArtworkArtistFactory(create_user=self.user)

        response = self.client.patch(
            f'/api/artwork/user/artist/{artist_2.id}/',
            data={
                'artist_name': artist.artist_name,
                'year_of_birth': artist.year_of_birth,
            },
            format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(),
                         {'non_field_errors': ['An artist with the same name, year of birth already exists.']})

    def test_should_allow_update_artist_if_user_is_not_owner(self):
        artist = ArtworkArtistFactory()

        response = self.client.patch(
            f'/api/artwork/user/artist/{artist.id}/',
            data={
                'artist_name': artist.artist_name,
                'year_of_birth': artist.year_of_birth,
            },
            format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'You do not have permission to edit this artist.'})
