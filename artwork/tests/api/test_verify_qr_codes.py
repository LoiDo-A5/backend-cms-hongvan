from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from common.tests.isolated_cache_test_case import APITestCase
from core.accounts.tests.api.base_user_test import BaseUserTest


class VerifyQrCodesApiTest(BaseUserTest):
    def setUp(self):
        super().setUp()
        artwork = ArtworkFactory()
        self.edition = ArtworkEditionFactory(artwork=artwork)
        self.certificate = ArtworkCertificateFactory(id=2, artwork_edition=self.edition,
                                                     code='b3ae3072-5bb6-4ce4-8cce-d3585e11725e')
        self.url = '/api/artwork/verify_qr_codes/'

    def test_verify_qr_codes(self):
        data = [
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 3, 'total_code': 3,
             'code': '02119f589cab582666e55d3788974e5d547b3a8faf7f99c043852e33d047be61'},
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 1, 'total_code': 3,
             'code': '833758e567fc87d06981a38f7dec532cea4b7931fe859612062dc27f5fa32c0c'},
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 2, 'total_code': 3,
             'code': 'b93bc2a3f188a528e3ac143ed46f93c9617fed2364e862fe2516cbfa6bba28e2'},

        ]

        response = self.client.post(
            '/api/artwork/verify_qr_codes/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['certificate_code'], self.certificate.code)

    def test_verify_qr_codes_no_qr_codes(self):
        response = self.client.post(self.url, [], format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'message': 'No QR codes provided'})

    def test_verify_qr_codes_codes_do_not_match(self):
        data = [
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 1, 'total_code': 1,
             'code': 'incorrect_code'},
        ]
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('QR codes do not match', response.data['message'])

    def test_verify_qr_codes_codes_count_mismatch(self):
        data = [
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 1, 'total_code': 5,
             'code': '02119f589cab582666e55d3788974e5d547b3a8faf7f99c043852e33d047be61'},
        ]
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Number of QR codes does not match the total code value', response.data['message'])

    def test_verify_qr_codes_edition_id_mismatch(self):
        data = [
            {'platform': 'gladius_art', 'edition_id': 999, 'order': 1, 'total_code': 1,
             'code': '02119f589cab582666e55d3788974e5d547b3a8faf7f99c043852e33d047be61'},
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 1, 'total_code': 3,
             'code': '833758e567fc87d06981a38f7dec532cea4b7931fe859612062dc27f5fa32c0c'},
        ]
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Edition id does not match', response.data['message'])

    def test_verify_qr_codes_some_codes_do_not_match(self):
        data = [
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 1, 'total_code': 3,
             'code': '833758e567fc87d06981a38f7dec532cea4b7931fe859612062dc27f5fa32c0c'},
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 2, 'total_code': 3,
             'code': 'incorrect_code'},
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 3, 'total_code': 3,
             'code': '02119f589cab582666e55d3788974e5d547b3a8faf7f99c043852e33d047be61'},
        ]
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('QR codes do not match', response.data['message'])


class ArtworkApiUnauthorizedTest(APITestCase):
    def setUp(self):
        super().setUp()
        artwork = ArtworkFactory()
        self.edition = ArtworkEditionFactory(artwork=artwork)
        self.certificate = ArtworkCertificateFactory(id=2, artwork_edition=self.edition,
                                                     code='b3ae3072-5bb6-4ce4-8cce-d3585e11725e')
        self.url = '/api/artwork/verify_qr_codes/'

    def test_verify_qr_codes(self):
        data = [
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 3, 'total_code': 3,
             'code': '02119f589cab582666e55d3788974e5d547b3a8faf7f99c043852e33d047be61'},
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 1, 'total_code': 3,
             'code': '833758e567fc87d06981a38f7dec532cea4b7931fe859612062dc27f5fa32c0c'},
            {'platform': 'gladius_art', 'edition_id': self.edition.id, 'order': 2, 'total_code': 3,
             'code': 'b93bc2a3f188a528e3ac143ed46f93c9617fed2364e862fe2516cbfa6bba28e2'},

        ]

        response = self.client.post(
            '/api/artwork/verify_qr_codes/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['certificate_code'], self.certificate.code)
