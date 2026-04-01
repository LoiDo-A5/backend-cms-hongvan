from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.certificate_request import CertificateRequestFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.image_artwork import ImageArtworkFactory
from artwork.factories.image_certificate_request import ImageCertificateRequestFactory
from artwork.factories.medium_artwork import MediumArtworkFactory
from artwork.factories.size_artwork import SizeArtworkFactory
from artwork.models import ImageCertificateRequest
from artwork.models.certificate_request import STATUS
from artwork.models.artwork_certificate import ArtworkCertificate
from artwork.models.owner_certificate import OwnerCertificate
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE

owner_info = {
    'name': 'John',
    'year_of_birth': '2021',
    'address': 'abc address',
}
shipping_info = {
    'recipient': 'John',
    'address': 'test address',
    'phone_number': '0909xxx',
}


class ArtworkCertificateApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.ARTIST
        self.user.save()

        self.collector = UserFactory(role=USER_ROLE.COLLECTOR)
        artwork_request = ArtworkFactory(status='available')
        artwork_edition_request = ArtworkEditionFactory(artwork=artwork_request, edition_number=1, status='available')

        self.certificate_request = CertificateRequestFactory(request_to=self.user, request_by=self.collector,
                                                             status=STATUS.REQUEST_RECEIVED, owner_info=owner_info,
                                                             shipping_info=shipping_info,
                                                             artwork_edition=artwork_edition_request)

    def test_user_approve_certificate_request(self):
        artist_artwork = ArtworkFactory(owner=self.user)
        artist_artwork_edition = ArtworkEditionFactory(artwork=artist_artwork, edition_number=1, status='available')

        artwork_edition_request = self.certificate_request.artwork_edition
        artwork_request = artwork_edition_request.artwork

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/approve_certificate_request/',
                                    data={
                                        'artwork_link_id': artist_artwork.id,
                                        'edition_link_number': artist_artwork_edition.edition_number,
                                    },
                                    format='json')

        artwork_request.refresh_from_db()
        artwork_edition_request.refresh_from_db()
        self.certificate_request.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        certificate = ArtworkCertificate.objects.first()

        self.assertEqual(self.certificate_request.status, STATUS.REQUEST_APPROVED)
        self.assertEqual(certificate.issued_by, self.user)
        self.assertEqual(certificate.issued_to, self.collector)
        self.assertEqual(certificate.artwork_edition, self.certificate_request.artwork_edition)

        self.assertEqual(artwork_request.linked_artwork, artist_artwork)
        self.assertEqual(artwork_edition_request.linked_edition, artist_artwork_edition)
        artist_artwork_edition.refresh_from_db()
        self.assertEqual(artwork_edition_request.status, 'available')

    def test_should_copy_artwork_when_approve_certificate_that_not_send_artwork_id(self):
        artwork_edition_request = self.certificate_request.artwork_edition
        artwork_request = artwork_edition_request.artwork
        artwork_request.total_edition = 5
        artwork_request.size = None
        artwork_request.save()

        ImageArtworkFactory(artwork=artwork_request)
        ImageArtworkFactory(artwork=artwork_request)

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/approve_certificate_request/',
                                    data={
                                        'artwork_link_id': None,
                                        'edition_link_number': 2,
                                    },
                                    format='json')

        artwork_request.refresh_from_db()
        artwork_edition_request.refresh_from_db()
        self.certificate_request.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        certificate = ArtworkCertificate.objects.first()
        new_artwork = self.user.artworks_owner.first()
        new_editions = new_artwork.editions.all()

        self.assertEqual(self.certificate_request.status, STATUS.REQUEST_APPROVED)
        self.assertEqual(certificate.issued_by, self.user)
        self.assertEqual(certificate.issued_to, self.collector)

        self.assertEqual(artwork_request.linked_artwork, new_artwork)
        self.assertEqual(new_artwork.status, 'available')
        self.assertTrue(new_artwork.is_public)
        self.assertEqual(len(new_editions), artwork_request.total_edition)
        self.assertEqual(artwork_edition_request.linked_edition.edition_number, 2)

    def test_should_create_new_medium_for_user_if_medium_is_custom(self):
        artwork_edition_request = self.certificate_request.artwork_edition
        artwork_request = artwork_edition_request.artwork
        artwork_request.total_edition = 5
        artwork_request.medium = MediumArtworkFactory(user=self.collector)
        artwork_request.save()

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/approve_certificate_request/',
                                    data={
                                        'edition_link_number': 2,
                                    },
                                    format='json')

        artwork_request.refresh_from_db()
        artwork_edition_request.refresh_from_db()
        self.certificate_request.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_artwork = self.user.artworks_owner.first()
        self.assertEqual(new_artwork.medium.user, self.user)

    def test_should_create_new_size_artwork_while_copy_artwork(self):
        artwork_edition_request = self.certificate_request.artwork_edition
        artwork_request = artwork_edition_request.artwork
        artwork_request.total_edition = 5
        artwork_request.size = SizeArtworkFactory()
        artwork_request.save()

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/approve_certificate_request/',
                                    data={
                                        'edition_link_number': 2,
                                    },
                                    format='json')

        artwork_request.refresh_from_db()
        artwork_edition_request.refresh_from_db()
        self.certificate_request.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_artwork = self.user.artworks_owner.first()
        self.assertEqual(new_artwork.size.width, artwork_request.size.width)

    def test_should_not_allow_approve_certificate_when_edition_already_has_certificate(self):
        artist_artwork = ArtworkFactory(owner=self.user)
        artist_artwork_edition = ArtworkEditionFactory(artwork=artist_artwork, edition_number=1)
        ArtworkCertificateFactory(artwork_edition=artist_artwork_edition)

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/approve_certificate_request/',
                                    data={
                                        'artwork_link_id': artist_artwork.id,
                                        'edition_link_number': artist_artwork_edition.edition_number,
                                    },
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), ['This edition already has certificate'])

    def test_should_not_allow_user_approve_certificate_request_if_not_has_permission(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        self.certificate_request.request_to = artist
        self.certificate_request.save()

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/approve_certificate_request/',
                                    format='json')

        self.certificate_request.refresh_from_db()
        certificate = ArtworkCertificate.objects.count()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.certificate_request.status, STATUS.REQUEST_RECEIVED)
        self.assertEqual(certificate, 0)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to approve this certificate request.'})

    def test_should_not_allow_user_approve_certificate_request_if_edition_already_has_certificate(self):
        self.certificate_request.status = STATUS.REQUEST_APPROVED
        self.certificate_request.save()
        edition = self.certificate_request.artwork_edition
        ArtworkCertificateFactory(artwork_edition=edition)

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/approve_certificate_request/',
                                    format='json')
        certificate = ArtworkCertificate.objects.count()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(certificate, 1)
        self.assertEqual(response.json(), {'detail': 'This artwork edition already has a certificate.'})

    def test_user_reject_certificate_request(self):
        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/reject_certificate_request/',
                                    data={
                                        'message': 'Not match data',
                                    },
                                    format='json')
        self.certificate_request.refresh_from_db()
        certificate = ArtworkCertificate.objects.count()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.certificate_request.status, STATUS.REQUEST_DENIED)
        self.assertEqual(self.certificate_request.message, 'Not match data')
        self.assertEqual(certificate, 0)

    def test_should_not_allow_user_reject_certificate_request_if_not_has_permission(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        self.certificate_request.request_to = artist
        self.certificate_request.save()

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/reject_certificate_request/',
                                    data={
                                        'message': 'Not match data',
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'You do not have permission to reject this certificate request.'})

    def test_should_not_allow_user_reject_certificate_request_if_edition_already_has_certificate(self):
        self.certificate_request.status = STATUS.REQUEST_APPROVED
        self.certificate_request.save()
        edition = self.certificate_request.artwork_edition
        ArtworkCertificateFactory(artwork_edition=edition)

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/reject_certificate_request/',
                                    format='json')
        certificate = ArtworkCertificate.objects.count()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(certificate, 1)
        self.assertEqual(response.json(), {'detail': 'This artwork edition already has a certificate.'})

    def test_review_certificate_request_valid_pk(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork_edition = ArtworkEditionFactory()
        certificate_request = CertificateRequestFactory(request_by=self.user, request_to=artist,
                                                        artwork_edition=artwork_edition)

        response = self.client.get(
            f'/api/artwork/certificate_request/{certificate_request.id}/review_certificate_request/',
            format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], certificate_request.id)
        self.assertEqual(response.data['edition']['id'], artwork_edition.id)

    def test_review_certificate_request_case_has_certificate(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork_edition = ArtworkEditionFactory()
        certificate_request = CertificateRequestFactory(request_by=self.user, request_to=artist,
                                                        artwork_edition=artwork_edition)
        ArtworkCertificateFactory(artwork_edition=artwork_edition)

        response = self.client.get(
            f'/api/artwork/certificate_request/{certificate_request.id}/review_certificate_request/',
            format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], certificate_request.id)
        self.assertEqual(response.data['edition']['id'], artwork_edition.id)
        self.assertIsNotNone(response.data['view_url'])

    def test_review_certificate_request_not_found(self):
        response = self.client.get('/api/artwork/certificate_request/9999/review_certificate_request/',
                                   format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'not found.')

    def test_review_certificate_request_wrong_method(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork_edition = ArtworkEditionFactory()
        certificate_request = CertificateRequestFactory(request_by=self.user, request_to=artist,
                                                        artwork_edition=artwork_edition)

        response = self.client.post(
            f'/api/artwork/certificate_request/{certificate_request.id}/review_certificate_request/',
            format='json')

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_certificate_request(self):
        certificate_request = CertificateRequestFactory(request_by=self.user, status=STATUS.REQUEST_DENIED)
        user = UserFactory(role=USER_ROLE.ARTIST)
        ImageCertificateRequestFactory(certificate_request=certificate_request)
        ImageCertificateRequestFactory(certificate_request=certificate_request)
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
        ]
        response = self.client.patch(
            f'/api/artwork/certificate_request/{certificate_request.id}/',
            {
                'shipping_info': shipping_info,
                'owner_info': owner_info,
                'request_to': user.id,
                'images': images,
            },
            format='json',
        )

        image_certificate_request = ImageCertificateRequest.objects.filter(certificate_request=certificate_request)
        certificate_request.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(certificate_request.shipping_info, shipping_info)
        self.assertEqual(certificate_request.owner_info, owner_info)
        self.assertEqual(certificate_request.request_to.id, user.id)
        self.assertEqual(certificate_request.status, STATUS.REQUEST_RECEIVED)

        self.assertEqual(image_certificate_request[0].image, images[0])
        self.assertEqual(image_certificate_request[1].image, images[1])

    def test_update_certificate_request_with_existing_images(self):
        certificate_request = CertificateRequestFactory(request_by=self.user, status=STATUS.REQUEST_DENIED)
        user = UserFactory(role=USER_ROLE.ARTIST)
        ImageCertificateRequestFactory(certificate_request=certificate_request, image='image_1.png')
        ImageCertificateRequestFactory(certificate_request=certificate_request)
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
        ]
        response = self.client.patch(
            f'/api/artwork/certificate_request/{certificate_request.id}/',
            {
                'shipping_info': shipping_info,
                'owner_info': owner_info,
                'request_to': user.id,
                'images': images,
            },
            format='json',
        )

        image_certificate_request = ImageCertificateRequest.objects.filter(certificate_request=certificate_request)
        certificate_request.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(certificate_request.shipping_info, shipping_info)
        self.assertEqual(certificate_request.owner_info, owner_info)
        self.assertEqual(certificate_request.request_to.id, user.id)
        self.assertEqual(certificate_request.status, STATUS.REQUEST_RECEIVED)

        self.assertEqual(image_certificate_request[0].image, images[0])
        self.assertEqual(image_certificate_request[1].image, images[1])

    def test_update_certificate_request_empty(self):
        certificate_request = CertificateRequestFactory(request_by=self.user, status=STATUS.REQUEST_DENIED)
        user = UserFactory(role=USER_ROLE.ARTIST)
        ImageCertificateRequestFactory(certificate_request=certificate_request)
        ImageCertificateRequestFactory(certificate_request=certificate_request)
        images = []
        response = self.client.patch(
            f'/api/artwork/certificate_request/{certificate_request.id}/',
            {
                'shipping_info': shipping_info,
                'owner_info': owner_info,
                'request_to': user.id,
                'images': images,
            },
            format='json',
        )

        image_certificate_request = ImageCertificateRequest.objects.filter(certificate_request=certificate_request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(image_certificate_request), 0)

    def test_validate_update_certificate_request(self):
        user = UserFactory(role=USER_ROLE.ARTIST)
        certificate_request = CertificateRequestFactory(request_by=user, status=STATUS.REQUEST_DENIED)
        response = self.client.patch(
            f'/api/artwork/certificate_request/{certificate_request.id}/',
            {
                'shipping_info': shipping_info,
                'owner_info': owner_info,
                'request_to': user.id,
                'status': STATUS.REQUEST_RECEIVED,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'Permission denied.')

    def test_update_status_edition_artwork_with_status_available(self):
        artist_artwork = ArtworkFactory(owner=self.user)
        artist_artwork_edition = ArtworkEditionFactory(artwork=artist_artwork, edition_number=1, status='available')

        artwork_edition_request = self.certificate_request.artwork_edition
        artwork_request = artwork_edition_request.artwork
        artwork_edition_request.status = 'available'
        artwork_request.status = 'available'
        artwork_edition_request.save()
        artwork_request.save()

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/approve_certificate_request/',
                                    data={
                                        'artwork_link_id': artist_artwork.id,
                                        'edition_link_number': artist_artwork_edition.edition_number,
                                    },
                                    format='json')

        artwork_request.refresh_from_db()
        artwork_edition_request.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(artwork_edition_request.status, 'available')
        self.assertEqual(artwork_request.status, 'available')

    def test_update_status_edition_artwork_with_status_lost(self):
        artist_artwork = ArtworkFactory(owner=self.user)
        artist_artwork_edition = ArtworkEditionFactory(artwork=artist_artwork, edition_number=1, status='available')

        artwork_edition_request = self.certificate_request.artwork_edition
        artwork_request = artwork_edition_request.artwork
        artwork_edition_request.status = 'lost'
        artwork_request.status = 'lost'
        artwork_edition_request.save()
        artwork_request.save()

        response = self.client.post(f'/api/artwork/certificate_request/{self.certificate_request.id}'
                                    f'/approve_certificate_request/',
                                    data={
                                        'artwork_link_id': artist_artwork.id,
                                        'edition_link_number': artist_artwork_edition.edition_number,
                                    },
                                    format='json')

        artwork_request.refresh_from_db()
        artwork_edition_request.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(artwork_edition_request.status, 'available')
        self.assertEqual(artwork_request.status, 'available')

    def test_approve_should_create_certificates_for_remaining_editions(self):
        artist_artwork = ArtworkFactory(owner=self.user)
        ArtworkEditionFactory(artwork=artist_artwork, edition_number=1, status='available')
        ArtworkEditionFactory(artwork=artist_artwork, edition_number=2, status='available')
        ArtworkEditionFactory(artwork=artist_artwork, edition_number=3, status='available')

        response = self.client.post(
            f'/api/artwork/certificate_request/{self.certificate_request.id}'
            f'/approve_certificate_request/',
            data={
                'artwork_link_id': artist_artwork.id,
                'edition_link_number': 1,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 1 certificate for the requested edition + 2 for remaining editions (2, 3)
        self.assertEqual(ArtworkCertificate.objects.count(), 3)

        remaining_certificates = ArtworkCertificate.objects.filter(
            issued_by=self.user,
            issued_to=self.user,
        )
        self.assertEqual(remaining_certificates.count(), 2)

        for cert in remaining_certificates:
            owner_cert = OwnerCertificate.objects.get(certificate=cert)
            self.assertEqual(owner_cert.user, self.user)
            cert.artwork_edition.refresh_from_db()
            self.assertEqual(cert.artwork_edition.status, 'available')
