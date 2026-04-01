from core.accounts.tests.api.base_user_test import BaseUserTest

from artwork.factories.artwork import ArtworkFactory


class SearchArtworkApi(BaseUserTest):
    def test_should_not_response_data_if_not_has_params_search(self):
        ArtworkFactory(owner=self.user)
        ArtworkFactory(owner=self.user)

        response = self.client.get('/api/artwork/search_autocomplete/', format='json')

        self.assertEqual(len(response.data), 0)

    def test_response_data_correctly(self):
        artwork_1 = ArtworkFactory(owner=self.user, title='String')
        artwork_2 = ArtworkFactory(owner=self.user, title='Spring')
        ArtworkFactory(owner=self.user, title='Summer')
        ArtworkFactory(owner=self.user, title='Winter')

        response = self.client.get('/api/artwork/search_autocomplete/', {
            'search': 'ing',
        }, format='json')

        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], artwork_2.id)
        self.assertEqual(response.data[1]['id'], artwork_1.id)

    def test_should_response_data_to_that_user_owner(self):
        artwork_1 = ArtworkFactory(owner=self.user, title='Spring')
        ArtworkFactory(title='Spring')

        response = self.client.get('/api/artwork/search_autocomplete/', {
            'search': 'ing',
            'owner': self.user.id,
        }, format='json')

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], artwork_1.id)
