from faker import Faker

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.image_artwork import ImageArtworkFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest

faker = Faker()


class ArtistApiTest(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_get_list_artists(self):
        user1 = UserFactory(role=1)
        user2 = UserFactory(role=1)
        user3 = UserFactory(role=1)
        UserFactory(role=2)
        artwork1 = ArtworkFactory(artist=user1)
        artwork2 = ArtworkFactory(artist=user2)
        ArtworkFactory(artist=user3)
        ArtworkFactory()
        ImageArtworkFactory(artwork=artwork1, image='image_1.png')
        ImageArtworkFactory(artwork=artwork2, image='image_2.png')
        ImageArtworkFactory(artwork=artwork2, image='image_3.png')

        response = self.client.get('/api/accounts/artist/', format='json')
        results = response.data['results']

        self.assertEqual(len(results), 3)

    def test_filter_by_search_name(self):
        user1 = UserFactory(role=1, name='John Doe')
        UserFactory(role=1, name='Alice Smith')
        UserFactory(role=1, name='Bob Smis')

        response = self.client.get('/api/accounts/artist/?search=John', format='json')
        results = response.data['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], user1.name)

    def test_filter_by_name_startswith(self):
        user1 = UserFactory(role=1, name='Liam')
        UserFactory(role=1, name='Alice Smith')
        UserFactory(role=1, name='Bob Smis')

        response = self.client.get('/api/accounts/artist/?name_startswith=Li', format='json')
        results = response.data['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], user1.name)
