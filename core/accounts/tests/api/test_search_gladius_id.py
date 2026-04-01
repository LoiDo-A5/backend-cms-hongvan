from faker import Faker

from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest
from rest_framework import status

faker = Faker()


class SearchUserGladiusIDTest(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_search_user_gladius_id_exact_uuid_should_return_user(self):
        user = UserFactory(uuid=faker.uuid4(), role=USER_ROLE.ARTIST)

        response = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': user.uuid,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], user.id)

    def test_search_user_gladius_id_only_accept_artist(self):
        user = UserFactory(uuid=faker.uuid4(), role=USER_ROLE.COLLECTOR)

        response = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': user.uuid,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_user_gladius_id_respects_role_in_collector(self):
        user = UserFactory(uuid=faker.uuid4(), role=USER_ROLE.COLLECTOR)

        response = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': user.uuid,
            'role__in': f'{USER_ROLE.COLLECTOR}',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], user.id)

    def test_search_user_gladius_id_strips_whitespace(self):
        user = UserFactory(uuid=faker.uuid4(), role=USER_ROLE.ARTIST)

        response = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': f'  {user.uuid}  ',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], user.id)

    def test_search_user_gladius_id_partial_uuid_should_return_empty(self):
        user = UserFactory(uuid=faker.uuid4(), role=USER_ROLE.ARTIST)
        partial_uuid = user.uuid[:8]

        response = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': partial_uuid,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_user_gladius_id_invalid_uuid_should_return_empty(self):
        UserFactory(uuid=faker.uuid4(), role=USER_ROLE.ARTIST)

        response = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': 'not-a-uuid',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_user_gladius_id_without_search_should_return_empty(self):
        UserFactory(uuid=faker.uuid4(), role=USER_ROLE.ARTIST)

        response = self.client.get('/api/accounts/search_user_gladius_id/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_user_gladius_id_search_only_whitespace_returns_empty(self):
        UserFactory(uuid=faker.uuid4(), role=USER_ROLE.ARTIST)

        response = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': '   \t  ',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_user_gladius_id_empty_role_in_defaults_to_artist_like_missing(self):
        user = UserFactory(uuid=faker.uuid4(), role=USER_ROLE.ARTIST)

        response = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': user.uuid,
            'role__in': '',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], user.id)

    def test_search_user_gladius_id_role_in_gallery_and_collector(self):
        collector = UserFactory(uuid=faker.uuid4(), role=USER_ROLE.COLLECTOR)
        gallery = UserFactory(uuid=faker.uuid4(), role=USER_ROLE.GALLERY_OWNER)

        r_collector = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': collector.uuid,
            'role__in': f'{USER_ROLE.GALLERY_OWNER},{USER_ROLE.COLLECTOR}',
        })
        r_gallery = self.client.get('/api/accounts/search_user_gladius_id/', {
            'search': gallery.uuid,
            'role__in': f'{USER_ROLE.GALLERY_OWNER},{USER_ROLE.COLLECTOR}',
        })

        self.assertEqual(r_collector.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r_collector.data), 1)
        self.assertEqual(r_collector.data[0]['id'], collector.id)

        self.assertEqual(r_gallery.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r_gallery.data), 1)
        self.assertEqual(r_gallery.data[0]['id'], gallery.id)
