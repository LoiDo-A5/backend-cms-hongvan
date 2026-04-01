from rest_framework import status

from artwork.factories.artist_tag_request import ArtistTagRequestFactory
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.utils.const import STATUS_REQUEST
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE


class ArtistTagRequestApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.ARTIST
        self.user.save()
        self.collector = UserFactory(role=USER_ROLE.COLLECTOR)
        self.tag_request = ArtistTagRequestFactory(request_to=self.user, request_by=self.collector,
                                                   status=STATUS_REQUEST.REQUEST_RECEIVED)

    def test_get_list_artist_tag_request(self):
        tag_request = ArtistTagRequestFactory(request_to=self.user)

        response = self.client.get('/api/artwork/artist_tag_request/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data['page_size'], 10)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['results']), 2)

        first_result = data['results'][0]
        self.assertEqual(first_result['id'], tag_request.id)
        self.assertEqual(first_result['artwork']['id'], tag_request.artwork.id)
        self.assertEqual(first_result['status'], tag_request.status)

    def test_filter_artist_tag_request_by_artwork(self):
        tag_request = ArtistTagRequestFactory(request_to=self.user)
        artwork = tag_request.artwork

        response = self.client.get('/api/artwork/artist_tag_request/', data={
            'artwork': artwork.id,
        }, format='json')

        data = response.data

        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['id'], tag_request.id)

    def test_filter_artist_tag_request_by_status(self):
        ArtistTagRequestFactory(request_to=self.user, status=STATUS_REQUEST.REQUEST_DENIED)
        tag_request_3 = ArtistTagRequestFactory(request_to=self.user, status=STATUS_REQUEST.REQUEST_APPROVED)

        response = self.client.get('/api/artwork/artist_tag_request/', data={
            'status__in': f'{STATUS_REQUEST.REQUEST_RECEIVED},{STATUS_REQUEST.REQUEST_APPROVED}',
        }, format='json')

        data = response.data

        self.assertEqual(len(data['results']), 2)
        self.assertEqual(data['results'][0]['id'], tag_request_3.id)
        self.assertEqual(data['results'][1]['id'], self.tag_request.id)

    def test_collector_filter(self):
        self.client.force_authenticate(user=self.collector)
        response = self.client.get('/api/artwork/artist_tag_request/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(len(data['results']), 1)

    def test_approve_artist_tag_request(self):
        collector_artwork = ArtworkFactory(owner=self.collector, total_edition=3)
        collector_artwork_edition = ArtworkEditionFactory(artwork=collector_artwork, edition_number=3)

        artist_artwork = ArtworkFactory(owner=self.user, total_edition=3)
        artist_artwork_edition = ArtworkEditionFactory(artwork=artist_artwork, edition_number=3)

        response = self.client.post(f'/api/artwork/artist_tag_request/{self.tag_request.id}'
                                    f'/approve_artist_tag_request/',
                                    data={
                                        'artwork_link_id': artist_artwork.id,
                                        'edition_link_number': artist_artwork_edition.edition_number,
                                        'requested_artwork_id': collector_artwork.id,
                                        'requested_edition_id': collector_artwork_edition.id,
                                    },
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tag_request.refresh_from_db()
        collector_artwork.refresh_from_db()
        collector_artwork_edition.refresh_from_db()
        self.assertEqual(self.tag_request.status, STATUS_REQUEST.REQUEST_APPROVED)
        self.assertEqual(collector_artwork.linked_artwork, artist_artwork)
        self.assertEqual(collector_artwork_edition.linked_edition, artist_artwork_edition)

    def test_should_not_approve_artist_tag_request_if_has_any_tag_already_approve(self):
        ArtistTagRequestFactory(artwork=self.tag_request.artwork, request_to=self.user,
                                status=STATUS_REQUEST.REQUEST_APPROVED)

        collector_artwork = ArtworkFactory(owner=self.collector, total_edition=3)
        collector_artwork_edition = ArtworkEditionFactory(artwork=collector_artwork, edition_number=3)

        artist_artwork = ArtworkFactory(owner=self.user, total_edition=3)
        artist_artwork_edition = ArtworkEditionFactory(artwork=artist_artwork, edition_number=3)

        response = self.client.post(f'/api/artwork/artist_tag_request/{self.tag_request.id}'
                                    f'/approve_artist_tag_request/',
                                    data={
                                        'artwork_link_id': artist_artwork.id,
                                        'edition_link_number': artist_artwork_edition.edition_number,
                                        'requested_artwork_id': collector_artwork.id,
                                        'requested_edition_id': collector_artwork_edition.id,
                                    },
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data[0], 'An approved request tag for this artwork already exists.')

    def test_should_copy_new_artwork_for_artist_if_not_send_artwork_link_id(self):
        collector_artwork = ArtworkFactory(owner=self.collector, total_edition=3, subject=None)
        collector_artwork_edition = ArtworkEditionFactory(artwork=collector_artwork, edition_number=3)

        response = self.client.post(f'/api/artwork/artist_tag_request/{self.tag_request.id}'
                                    f'/approve_artist_tag_request/',
                                    data={
                                        'artwork_link_id': None,
                                        'edition_link_number': 3,
                                        'requested_artwork_id': collector_artwork.id,
                                        'requested_edition_id': collector_artwork_edition.id,
                                    },
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tag_request.refresh_from_db()
        collector_artwork.refresh_from_db()
        collector_artwork_edition.refresh_from_db()
        self.assertEqual(self.tag_request.status, STATUS_REQUEST.REQUEST_APPROVED)

        self.assertIsNotNone(collector_artwork.linked_artwork)
        self.assertIsNotNone(collector_artwork_edition.linked_edition)

        copy_artwork = collector_artwork.linked_artwork
        copy_edition = collector_artwork_edition.linked_edition
        self.assertEqual(copy_artwork.owner, self.user)
        self.assertEqual(copy_edition.artwork, copy_artwork)

    def test_approve_artist_tag_request_no_permission(self):
        collector = UserFactory(role=USER_ROLE.COLLECTOR)

        artwork_request = ArtworkFactory(status='available')
        tag_request = ArtistTagRequestFactory(request_to=collector, request_by=collector,
                                              status=STATUS_REQUEST.REQUEST_RECEIVED,
                                              artwork=artwork_request)
        response = self.client.post(f'/api/artwork/artist_tag_request/{tag_request.id}'
                                    f'/approve_artist_tag_request/',
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to approve this request.'})

    def test_user_reject_artist_tag_request(self):
        response = self.client.post(f'/api/artwork/artist_tag_request/{self.tag_request.id}'
                                    f'/reject_artist_tag_request/',
                                    data={
                                        'message': 'Not match data',
                                    },
                                    format='json')
        self.tag_request.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.tag_request.status, STATUS_REQUEST.REQUEST_DENIED)
        self.assertEqual(self.tag_request.message, 'Not match data')

    def test_reject_artist_tag_request_no_permission(self):
        collector = UserFactory(role=USER_ROLE.COLLECTOR)
        artwork_request = ArtworkFactory(status='available')
        tag_request = ArtistTagRequestFactory(request_to=collector, request_by=collector,
                                              status=STATUS_REQUEST.REQUEST_RECEIVED,
                                              artwork=artwork_request)
        response = self.client.post(f'/api/artwork/artist_tag_request/{tag_request.id}'
                                    f'/reject_artist_tag_request/',
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to approve this request.'})

    def test_user_resend_artist_tag_request(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork_request = ArtworkFactory(status='available')
        tag_request = ArtistTagRequestFactory(request_to=artist, request_by=self.user,
                                              status=STATUS_REQUEST.REQUEST_DENIED,
                                              artwork=artwork_request)
        response = self.client.post(f'/api/artwork/artist_tag_request/{tag_request.id}'
                                    f'/resend_artist_tag_request/',
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tag_request.refresh_from_db()
        self.assertEqual(self.tag_request.status, STATUS_REQUEST.REQUEST_RECEIVED)

    def test_resend_artist_tag_request_no_permission(self):
        artist = UserFactory(role=USER_ROLE.COLLECTOR)
        artwork_request = ArtworkFactory(status='available')
        tag_request = ArtistTagRequestFactory(request_to=artist, request_by=artist,
                                              status=STATUS_REQUEST.REQUEST_RECEIVED,
                                              artwork=artwork_request)
        response = self.client.post(f'/api/artwork/artist_tag_request/{tag_request.id}'
                                    f'/resend_artist_tag_request/',
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to approve this request.'})

    def test_cancel_artist_tag_request(self):
        self.client.force_authenticate(user=self.collector)
        response = self.client.post(f'/api/artwork/artist_tag_request/{self.tag_request.id}'
                                    f'/cancel_artist_tag_request/',
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tag_request.refresh_from_db()
        self.assertEqual(self.tag_request.status, STATUS_REQUEST.REQUEST_CANCELED)
        self.assertEqual(self.tag_request.artwork.artist_name, '')

    def test_cancel_artist_tag_request_no_permission(self):
        another_collector = UserFactory(role=USER_ROLE.COLLECTOR)
        self.client.force_authenticate(user=another_collector)
        response = self.client.post(f'/api/artwork/artist_tag_request/{self.tag_request.id}'
                                    f'/cancel_artist_tag_request/',
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(), {'detail': 'You do not have permission to cancel this request.'})

    def test_review_certificate_request_valid_pk(self):
        response = self.client.get(
            f'/api/artwork/artist_tag_request/{self.tag_request.id}/review_artist_tag_request/',
            format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.tag_request.id)

    def test_review_artist_tag_request_invalid_pk(self):
        response = self.client.get('/api/artwork/artist_tag_request/99999/review_artist_tag_request/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
