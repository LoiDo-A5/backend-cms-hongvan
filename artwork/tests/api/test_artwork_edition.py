from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.image_artwork import ImageArtworkFactory
from artwork.factories.owner_certificate import OwnerCertificateFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ArtworkEditionApiTest(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_get_list_artwork_edition(self):
        ArtworkFactory(owner=self.user)
        artwork1 = ArtworkFactory(owner=self.user)
        artwork2 = ArtworkFactory(owner=self.user)

        ImageArtworkFactory(artwork=artwork1)
        ImageArtworkFactory(artwork=artwork2)

        edition_1 = ArtworkEditionFactory(artwork=artwork1)
        edition_2 = ArtworkEditionFactory(artwork=artwork1)
        edition_3 = ArtworkEditionFactory(artwork=artwork2)

        certificate1 = ArtworkCertificateFactory(artwork_edition=edition_1)
        certificate3 = ArtworkCertificateFactory(artwork_edition=edition_3)
        owner_certificate = OwnerCertificateFactory(certificate=certificate1)

        response = self.client.get('/api/artwork/edition/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['results'][0]['title'], artwork2.title)
        self.assertEqual(response.data['results'][0]['total_edition'], artwork2.total_edition)
        self.assertEqual(response.data['results'][1]['title'], artwork1.title)
        self.assertEqual(response.data['results'][1]['total_edition'], artwork1.total_edition)

        self.assertEqual(len(response.data['results'][0]['editions']), 1)
        self.assertEqual(len(response.data['results'][1]['editions']), 2)
        self.assertEqual(response.data['results'][0]['editions'][0]['edition_number'], edition_3.edition_number)
        self.assertEqual(response.data['results'][1]['editions'][1]['edition_number'], edition_2.edition_number)
        self.assertEqual(response.data['results'][1]['editions'][0]['edition_number'], edition_1.edition_number)

        self.assertEqual(response.data['results'][0]['editions'][0]['id_certificate'], certificate3.code)
        self.assertEqual(response.data['results'][1]['editions'][0]['id_certificate'], certificate1.code)
        self.assertEqual(response.data['results'][1]['editions'][0]['owner_certificate']['name'],
                         owner_certificate.name)

    def test_get_list_artwork_edition_with_edition_linked(self):
        artwork = ArtworkFactory(owner=self.user)

        edition_1 = ArtworkEditionFactory(artwork=artwork)
        ArtworkEditionFactory(artwork=artwork)

        edition_2 = ArtworkEditionFactory(linked_edition=edition_1)
        certificate_linked = ArtworkCertificateFactory(artwork_edition=edition_2)

        response = self.client.get('/api/artwork/edition/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        editions = response.data['results'][0]['editions']
        self.assertEqual(len(editions), 2)

        self.assertEqual(editions[0]['id_certificate'], certificate_linked.code)

    def test_search_artwork_by_title(self):
        artwork1 = ArtworkFactory(title='Sunset Painting', owner=self.user)
        artwork2 = ArtworkFactory(title='Ocean View', owner=self.user)
        ArtworkFactory(title='Mountain Landscape', owner=self.user)

        ArtworkEditionFactory(artwork=artwork1)
        ArtworkEditionFactory(artwork=artwork2)

        search_query = 'Ocean'
        response = self.client.get(f'/api/artwork/edition/?search={search_query}', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertTrue(all('Ocean' in artwork['title'] for artwork in results))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], artwork2.title)
