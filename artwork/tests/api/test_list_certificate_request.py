from rest_framework import status

from artwork.factories.certificate_request import CertificateRequestFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


class ListCertificatrRequestApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        self.certificate_request = CertificateRequestFactory(request_by=self.user)
        self.edition = self.certificate_request.artwork_edition
        self.artwork = self.edition.artwork

    def test_get_list_certificate_request_by_role_collector_success(self):
        CertificateRequestFactory()
        response = self.client.get('/api/artwork/list_certificate_request/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        self.assertEqual(len(results), 1)
        data = results[0]
        artwork = data['artwork']
        self.assertEqual(data['edition']['id'], self.edition.id)
        self.assertEqual(artwork['total_edition'], self.artwork.total_edition)
        self.assertEqual(data['request_by']['name'], self.certificate_request.request_by.name)

    def test_get_list_certificate_request_by_role_artist_success(self):
        self.user.role = USER_ROLE.ARTIST
        self.user.save()
        self.certificate_request.request_to = self.user
        self.certificate_request.save()
        CertificateRequestFactory()
        response = self.client.get('/api/artwork/list_certificate_request/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        self.assertEqual(len(results), 1)
        data = results[0]
        artwork = data['artwork']
        self.assertEqual(data['edition']['id'], self.edition.id)
        self.assertEqual(artwork['total_edition'], self.artwork.total_edition)

    def test_get_list_certificate_request_by_role_service_provider(self):
        self.user.role = USER_ROLE.SERVICE_PROVIDER
        self.user.save()
        self.certificate_request.request_to = self.user
        self.certificate_request.save()
        CertificateRequestFactory()
        response = self.client.get('/api/artwork/list_certificate_request/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        self.assertEqual(len(results), 0)
