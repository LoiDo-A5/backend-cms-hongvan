from rest_framework import status

from artwork.factories.owner_certificate import OwnerCertificateFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.models.user import USER_ROLE


class ArtworkCertificateApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        self.owner_certificate = OwnerCertificateFactory()
        self.certificate = self.owner_certificate.certificate
        self.certificate.issued_to = self.user
        self.certificate.save()

        self.edition = self.certificate.artwork_edition
        self.artwork = self.edition.artwork

        self.artwork.owner = self.user
        self.artwork.save()

    def test_artist_get_list_certificate(self):
        self.user.role = USER_ROLE.ARTIST
        self.user.save()
        collector = UserFactory()

        certificate_1 = ArtworkCertificateFactory(issued_by=self.user, issued_to=self.user)
        certificate_2 = ArtworkCertificateFactory(issued_by=self.user, issued_to=collector)
        ArtworkCertificateFactory()

        response = self.client.get('/api/artwork/certificate/', format='json')
        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['code'], str(certificate_2.code))
        self.assertEqual(results[1]['code'], str(certificate_1.code))

    def test_get_certificate_success(self):
        ArtworkCertificateFactory(issued_to=self.user)
        ArtworkCertificateFactory()

        response = self.client.get('/api/artwork/certificate/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        self.assertEqual(len(results), 2)

        data = results[1]
        artwork = data['artwork']

        self.assertEqual(data['code'], str(self.certificate.code))
        self.assertEqual(data['edition_number'], self.edition.edition_number)

        self.assertEqual(artwork['owner'], self.user.id)
        self.assertEqual(artwork['total_edition'], self.artwork.total_edition)

    def test_get_certificate_search_by_artwork_name(self):
        certificate = ArtworkCertificateFactory(issued_to=self.user)
        artwork = certificate.artwork_edition.artwork
        artwork.title = 'Galadius'
        artwork.save()

        response = self.client.get(
            '/api/artwork/certificate/',
            data={
                'search': 'Gala',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)

        data = results[0]
        artwork_response = data['artwork']

        self.assertEqual(len(results), 1)
        self.assertEqual(data['code'], str(certificate.code))
        self.assertEqual(artwork_response['title'], artwork.title)
