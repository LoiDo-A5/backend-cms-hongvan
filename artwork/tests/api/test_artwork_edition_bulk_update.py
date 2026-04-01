from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from core.accounts.factories.user import UserLocationFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ArtworkEditionStatusApiTest(BaseUserTest):
    def test_bulk_update_artwork_editions_updates_artwork_status(self):
        location1 = UserLocationFactory(user=self.user)
        location2 = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, total_edition=5)
        edition_1 = ArtworkEditionFactory(artwork=artwork)
        edition_2 = ArtworkEditionFactory(artwork=artwork)

        data = [
            {'id': edition_1.id, 'status': 'sold', 'location': location1.id},
            {'id': edition_2.id, 'status': 'available', 'location': location2.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        edition_1.refresh_from_db()
        edition_2.refresh_from_db()
        artwork.refresh_from_db()

        self.assertEqual(edition_1.status, 'sold')
        self.assertEqual(edition_1.location.id, location1.id)
        self.assertEqual(edition_2.status, 'available')
        self.assertEqual(edition_2.location.id, location2.id)

        self.assertEqual(artwork.status, 'available')

    def test_bulk_update_artwork_editions_with_invalid_data(self):
        location1 = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, total_edition=5)
        edition_1 = ArtworkEditionFactory(artwork=artwork)
        edition_2 = ArtworkEditionFactory(artwork=artwork)

        data = [
            {'id': edition_1.id, 'status': 'invalid_status', 'location': location1.id},
            {'id': edition_2.id, 'status': 'available', 'location': location1.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)

        edition_1.refresh_from_db()
        edition_2.refresh_from_db()
        self.assertNotEqual(edition_1.status, 'invalid_status')
        self.assertNotEqual(edition_2.status, 'invalid_status')

    def test_bulk_update_all_editions_same_status(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user)
        edition_1 = ArtworkEditionFactory(artwork=artwork, status='consignment')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='consignment')

        data = [
            {'id': edition_1.id, 'status': 'lost', 'location': location.id},
            {'id': edition_2.id, 'status': 'lost', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'not_for_sale')

    def test_bulk_update_mixed_statuses_including_sold(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user)
        edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='sold')

        data = [
            {'id': edition_1.id, 'status': 'available', 'location': location.id},
            {'id': edition_2.id, 'status': 'sold', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'available')

    def test_no_effective_status_change(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='available')
        edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='available')

        data = [
            {'id': edition_1.id, 'status': 'available', 'location': location.id},
            {'id': edition_2.id, 'status': 'available', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'available')

    def test_bulk_update_all_editions_sold(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user)
        edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='available')

        data = [
            {'id': edition_1.id, 'status': 'sold', 'location': location.id},
            {'id': edition_2.id, 'status': 'sold', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'sold')

    def test_artwork_status_change_to_first_edition_status(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='not_for_sale')
        edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='lost')

        data = [
            {'id': edition_1.id, 'status': 'consignment', 'location': location.id},
            {'id': edition_2.id, 'status': 'donated_gifted', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'available')

    def test_bulk_update_all_editions_sold_no_available_consignment(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user)
        edition_1 = ArtworkEditionFactory(artwork=artwork, status='not_for_sale')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='lost')
        ArtworkEditionFactory(artwork=artwork, status='not_for_sale')
        ArtworkEditionFactory(artwork=artwork, status='not_for_sale')

        data = [
            {'id': edition_1.id, 'status': 'sold', 'location': location.id},
            {'id': edition_2.id, 'status': 'not_for_sale', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'sold')

    def test_bulk_update_no_matching_artwork_status(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='not_for_sale')
        edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='lost')
        ArtworkEditionFactory(artwork=artwork, status='lost')
        ArtworkEditionFactory(artwork=artwork, status='lost')

        data = [
            {'id': edition_1.id, 'status': 'under_maintenance', 'location': location.id},
            {'id': edition_2.id, 'status': 'under_maintenance', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'not_for_sale')

    def test_bulk_update_with_data_empty(self):
        artwork = ArtworkFactory(artist=self.user, status='not_for_sale')
        ArtworkEditionFactory(artwork=artwork, status='available')
        ArtworkEditionFactory(artwork=artwork, status='lost')
        ArtworkEditionFactory(artwork=artwork, status='lost')
        ArtworkEditionFactory(artwork=artwork, status='lost')

        data = []

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'not_for_sale')

    def test_artwork_status_not_in_updated_editions_statuses(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='on_display')
        edition_1 = ArtworkEditionFactory(status='available')
        edition_2 = ArtworkEditionFactory(status='lost')

        data = [
            {'id': edition_1.id, 'status': 'lost', 'location': location.id},
            {'id': edition_2.id, 'status': 'lost', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()

        self.assertEqual(artwork.status, 'on_display')
        self.assertIn(artwork.status, ['on_display'])

    def test_artwork_status_not_in_updated_editions_empty_status_list(self):
        artwork = ArtworkFactory(artist=self.user, status='on_display')
        ArtworkEditionFactory(artwork=artwork, status='available')
        ArtworkEditionFactory(artwork=artwork, status='sold')

        data = []

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'on_display')

    def test_artwork_status_unchanged_when_no_edition_statuses(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='available')

        edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='available')

        data = [
            {'id': edition_1.id, 'status': 'available', 'location': location.id},
            {'id': edition_2.id, 'status': 'available', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'available')

    def test_artwork_status_when_update_edition_status_donated_gifted(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='available')

        edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='available')

        data = [
            {'id': edition_1.id, 'status': 'donated_gifted', 'location': location.id},
            {'id': edition_2.id, 'status': 'donated_gifted', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.status, 'donated_gifted')

    def test_bulk_update_case_editions_total_1(self):
        location = UserLocationFactory(user=self.user)
        artwork = ArtworkFactory(artist=self.user, status='available')

        edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')

        data = [
            {'id': edition_1.id, 'status': 'donated_gifted', 'location': location.id},
        ]

        response = self.client.put(
            '/api/artwork/editions/bulk_update/',
            data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        artwork.refresh_from_db()
        self.assertEqual(artwork.location.location, location.location)
