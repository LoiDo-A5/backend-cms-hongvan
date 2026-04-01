from rest_framework import status
from rest_framework.response import Response

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.models import ArtworkEdition
from activity_log.models.artwork_log import ArtworkLog, ACTION_UPDATE_ARTWORK
from core.accounts.factories.user import UserLocationFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest
from unittest import mock
from unittest.mock import PropertyMock


class ArtworkEditionApiTest(BaseUserTest):
    def test_update_edition_owner_name_currency_price(self):
        artwork = ArtworkFactory(artist=self.user)
        edition = ArtworkEditionFactory(
            artwork=artwork,
            owner_name=None,
            currency='vnd',
            price=None,
        )

        payload = {
            'owner_name': 'Nguyen Van A',
            'currency': 'usd',
            'price': '1500.00',
        }

        response = self.client.patch(
            f'/api/artwork/edition/{edition.id}/',
            payload,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        edition.refresh_from_db()
        self.assertEqual(edition.owner_name, payload['owner_name'])
        self.assertEqual(edition.currency, payload['currency'])
        self.assertEqual(str(edition.price), payload['price'])

        logs = ArtworkLog.objects.filter(artwork_id=artwork.id, action_type=ACTION_UPDATE_ARTWORK)
        self.assertTrue(logs.exists())

    def test_update_edition_with_available_and_consignment_statuses(self):
        user_location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user)
        ArtworkEditionFactory(artwork=artwork, status='consignment')
        edition2 = ArtworkEditionFactory(artwork=artwork, status='available')
        response = self.client.patch(
            f'/api/artwork/edition/{edition2.id}/',
            {
                'status': 'consignment',
                'location': user_location.id,
            },
            format='json')

        artwork.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(artwork.status, 'available')

    def test_update_all_editions_to_same_status(self):
        user_location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user)
        edition = ArtworkEditionFactory(artwork=artwork, status='under_maintenance')
        response = self.client.patch(
            f'/api/artwork/edition/{edition.id}/',
            {
                'status': 'sold',
                'location': user_location.id,
            },
            format='json')

        artwork.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(artwork.status, 'sold')

    def test_update_edition_with_sold_and_mixed_statuses(self):
        user_location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user)
        edition1 = ArtworkEditionFactory(artwork=artwork, status='donated_gifted')
        ArtworkEditionFactory(artwork=artwork, status='sold')
        response = self.client.patch(
            f'/api/artwork/edition/{edition1.id}/',
            {
                'status': 'donated_gifted',
                'location': user_location.id,
            },
            format='json')

        artwork.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(artwork.status, 'sold')

    def test_update_edition_fallback_status(self):
        user_location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user)
        ArtworkEditionFactory(artwork=artwork, status='lost')
        edition2 = ArtworkEditionFactory(artwork=artwork, status='not_for_sale')
        response = self.client.patch(
            f'/api/artwork/edition/{edition2.id}/',
            {
                'status': 'lost',
                'location': user_location.id,
            },
            format='json')

        artwork.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(artwork.status, 'not_for_sale')

    def test_update_edition_invalid_data(self):
        user_location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='sold')
        edition = ArtworkEditionFactory(artwork=artwork, status='available')

        response = self.client.patch(
            f'/api/artwork/edition/{edition.id}/',
            {
                'status': 'invalid_status',
                'location': user_location.id,
            },
            format='json')

        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'sold')

    def test_update_edition_fails_no_change(self):
        user_location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='available')
        edition = ArtworkEditionFactory(artwork=artwork, status='available')

        with mock.patch('rest_framework.mixins.UpdateModelMixin.update',
                        return_value=Response({'error': 'Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)):
            response = self.client.patch(
                f'/api/artwork/edition/{edition.id}/',
                {
                    'status': 'sold',
                    'location': user_location.id,
                },
                format='json')

            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

            artwork.refresh_from_db()
            self.assertEqual(artwork.status, 'available')

    def test_update_edition_status_updates_artwork(self):
        user_location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user)
        edition = ArtworkEditionFactory(artwork=artwork, status='available')

        response = self.client.patch(
            f'/api/artwork/edition/{edition.id}/',
            {'status': 'lost', 'location': user_location.id},
            format='json')

        artwork.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(artwork.status, 'not_for_sale')

    def test_update_edition_retains_status_when_no_editions(self):
        user_location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='available')
        edition = ArtworkEditionFactory(artwork=artwork, status='available')

        with mock.patch.object(type(artwork), 'editions', new_callable=PropertyMock) as mocked_editions:
            mocked_editions.return_value.all.return_value = []
            response = self.client.patch(
                f'/api/artwork/edition/{edition.id}/',
                {'status': 'lost', 'location': user_location.id},
                format='json')

            artwork.refresh_from_db()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(artwork.status, 'not_for_sale')

    def test_update_edition_status_donated_gifted(self):
        user_location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='sold')
        edition = ArtworkEditionFactory(artwork=artwork, status='available')

        response = self.client.patch(
            f'/api/artwork/edition/{edition.id}/',
            {
                'status': 'donated_gifted',
                'location': user_location.id,
            },
            format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'donated_gifted')

    def test_delete_artwork_edition(self):
        self.user.role = USER_ROLE.ARTIST
        self.user.save()
        artwork = ArtworkFactory(artist=self.user)
        edition = ArtworkEditionFactory(artwork=artwork, status='under_maintenance')
        response = self.client.delete(
            f'/api/artwork/edition/{edition.id}/delete/',
            format='json')

        artwork.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ArtworkEdition.objects.filter(id=edition.id).exists())

    def test_delete_artwork_edition_case_request_not_role_artist(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artwork = ArtworkFactory(artist=self.user)
        edition = ArtworkEditionFactory(artwork=artwork, status='under_maintenance')

        response = self.client.delete(
            f'/api/artwork/edition/{edition.id}/delete/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            ['Only users with the artist role can delete this edition.'],
        )

    def test_delete_artwork_edition_case_edition_has_certificate(self):
        self.user.role = USER_ROLE.ARTIST
        self.user.save()

        artwork = ArtworkFactory(artist=self.user)
        edition = ArtworkEditionFactory(artwork=artwork, status='under_maintenance')
        ArtworkCertificateFactory(artwork_edition=edition)

        response = self.client.delete(
            f'/api/artwork/edition/{edition.id}/delete/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            ['Cannot delete edition because it has an associated certificate.'],
        )
