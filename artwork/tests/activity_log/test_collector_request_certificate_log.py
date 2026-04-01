from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.medium_artwork import MediumArtworkFactory
from artwork.factories.image_artwork import ImageArtworkFactory
from activity_log.models.artwork_log import ArtworkLog, ACTION_CERTIFICATE_REQUESTED
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE


class CollectorRequestCertificateLogTest(BaseUserTest):
    def test_collector_request_certificate_creates_activity_logs(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist = UserFactory(role=USER_ROLE.ARTIST, name='Artist Name')
        medium = MediumArtworkFactory(category='painting', user=UserFactory())
        artwork = ArtworkFactory(owner=self.user, status='available', size=None, total_edition=3, title='Test Artwork')
        ImageArtworkFactory(artwork=artwork)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1, status='available')

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.uuid}/request_certificate/',
            {
                'artwork': {
                    'uuid': str(artwork.uuid),
                    'id': artwork.id,
                    'title': 'Test Artwork',
                    'size': {
                        'height': 1,
                        'width': 1,
                        'depth': 1,
                    },
                    'year_created': 2021,
                    'edition_number': 1,
                    'total_edition': 3,
                    'medium': {
                        'id': medium.id,
                        'name': medium.name,
                        'name_vi': medium.name_vi,
                        'category': medium.category,
                        'user': medium.user.id,
                    },
                },
                'edition': {
                    'id': edition.id,
                    'edition_number': 1,
                    'status': edition.status,
                    'location': edition.location.id,
                    'linked_edition': None,
                },
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
                'request_to': artist.id,
                'images': ['cert_image_1.png'],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        logs = ArtworkLog.objects.filter(
            artwork_id=artwork.id,
            action_type=ACTION_CERTIFICATE_REQUESTED,
        ).order_by('id')
        self.assertEqual(logs.count(), 2)

        log_request_by = logs[0]
        self.assertEqual(log_request_by.user, self.user)
        expected_template_en_1 = 'Requested certificate for artwork {title} (to artist: {artist})'
        expected_template_vi_1 = 'Đã yêu cầu chứng nhận cho tác phẩm {title} (tới nghệ sĩ: {artist})'
        expected_params_1 = {
            'field': 'certificate_request',
            'title': 'Test Artwork',
            'artist': 'Artist Name',
        }
        expected_content_en_1 = expected_template_en_1.format(**expected_params_1)
        expected_content_vi_1 = expected_template_vi_1.format(**expected_params_1)

        self.assertEqual(log_request_by.template_en, expected_template_en_1)
        self.assertEqual(log_request_by.template_vi, expected_template_vi_1)
        self.assertEqual(log_request_by.content_en, expected_content_en_1)
        self.assertEqual(log_request_by.content_vi, expected_content_vi_1)
        self.assertEqual(log_request_by.params, expected_params_1)

        log_request_to = logs[1]
        self.assertEqual(log_request_to.user, artist)
        expected_template_en_2 = 'Certificate request received for artwork {title} (from: {request_by}).'
        expected_template_vi_2 = 'Đã nhận yêu cầu chứng nhận cho tác phẩm {title} (từ: {request_by}).'
        expected_params_2 = {
            'field': 'certificate_request',
            'title': 'Test Artwork',
            'request_by': self.user.name,
        }
        expected_content_en_2 = expected_template_en_2.format(**expected_params_2)
        expected_content_vi_2 = expected_template_vi_2.format(**expected_params_2)

        self.assertEqual(log_request_to.template_en, expected_template_en_2)
        self.assertEqual(log_request_to.template_vi, expected_template_vi_2)
        self.assertEqual(log_request_to.content_en, expected_content_en_2)
        self.assertEqual(log_request_to.content_vi, expected_content_vi_2)
        self.assertEqual(log_request_to.params, expected_params_2)
