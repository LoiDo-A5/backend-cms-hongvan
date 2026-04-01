from rest_framework import status
from unittest import mock
from core.accounts.factories.user import UserSignalIdFactory

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.medium_artwork import MediumArtworkFactory
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


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


class NotificationReceiveCertificateTest(BaseUserTest):
    @mock.patch('core.accounts.tasks.notification.Client.send_notification')
    def test_send_notification_certificate_request(self, send_one_signal):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=self.user, status='available', size=None, total_edition=3, title='Artwork 1')
        medium = MediumArtworkFactory(category='painting', user=UserFactory())
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1, status='available')

        images = [
            'image_1.png',
            'image_2.png',
        ]
        user_signal = UserSignalIdFactory(user=artist)

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.uuid}/request_certificate/',
            {
                'artwork': {
                    'uuid': str(artwork.uuid),
                    'id': artwork.id,
                    'title': 'Mountain',
                    'size': {
                        'height': 1,
                        'width': 1,
                        'depth': 1,
                    },
                    'year_created': 2021,
                    'edition_number': 1,
                    'total_edition': 10,
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
                    'edition_number': 2,
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
                'images': images,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_notification = {
            'contents': {'en': f'{self.user.name} requested a certificate of the artwork Mountain.'},
            'headings': {'en': 'Gladius Art'},
            'include_player_ids': [user_signal.signal_id],
            'android': {
                'priority': 'high',
            },
            'priority': 10,
            'content_available': True,
            'data': {
                'content_code': 'RECEIVE_CERTIFICATE_REQUEST',
                'params': {
                    'certificate_request_id': response.data['id'],
                },
            },
        }
        send_one_signal.assert_called_with(new_notification)
