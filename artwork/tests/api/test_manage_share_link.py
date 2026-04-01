from datetime import timedelta

from django.utils import timezone
from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.share_link import ShareLinkFactory
from artwork.models import ShareLink
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ManageShareLinkListAPIViewTest(BaseUserTest):
    """Tests for ManageShareLinkListAPIView covering get_queryset and paginated response."""

    def setUp(self):
        super().setUp()
        self.artwork = ArtworkFactory(owner=self.user, is_public=True)

    def test_list_default_tab_excludes_artwork_type(self):
        ShareLinkFactory(user=self.user, share_type='mixed')
        ShareLinkFactory(user=self.user, share_type='exhibition')
        ShareLinkFactory(user=self.user, share_type='artwork')

        response = self.client.get('/api/artwork/manage_share_links/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        share_types = [r['share_type'] for r in response.data['results']]
        self.assertNotIn('artwork', share_types)

    def test_list_selected_artworks_tab_filters_artwork_type(self):
        ShareLinkFactory(user=self.user, share_type='artwork')
        ShareLinkFactory(user=self.user, share_type='mixed')

        response = self.client.get('/api/artwork/manage_share_links/?tab=selected_artworks')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['share_type'], 'artwork')

    def test_list_returns_paginated_response_with_all_fields(self):
        ShareLinkFactory(user=self.user, share_type='mixed')

        response = self.client.get('/api/artwork/manage_share_links/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('page_size', response.data)
        self.assertIn('count', response.data)
        self.assertIn('total_pages', response.data)
        self.assertIn('current_page', response.data)
        self.assertIn('results', response.data)

    def test_list_only_returns_own_share_links(self):
        other_user = UserFactory()
        ShareLinkFactory(user=self.user, share_type='mixed')
        ShareLinkFactory(user=other_user, share_type='mixed')

        response = self.client.get('/api/artwork/manage_share_links/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)


class ManageShareLinkSerializerFieldsTest(BaseUserTest):
    """Tests for ManageShareLinkSerializer computed fields."""

    def setUp(self):
        super().setUp()
        self.artwork1 = ArtworkFactory(owner=self.user, is_public=True)
        self.artwork2 = ArtworkFactory(owner=self.user, is_public=True)

    def test_share_url_field(self):
        link = ShareLinkFactory(user=self.user, share_type='mixed')

        response = self.client.get('/api/artwork/manage_share_links/')

        result = response.data['results'][0]
        self.assertIn(str(link.id), result['share_url'])
        self.assertIn('/share/', result['share_url'])

    def test_artwork_count_when_not_share_all(self):
        link = ShareLinkFactory(user=self.user, share_type='mixed', is_share_all=False)
        link.artwork.add(self.artwork1, self.artwork2)

        response = self.client.get('/api/artwork/manage_share_links/')

        result = response.data['results'][0]
        self.assertEqual(result['artwork_count'], 2)

    def test_artwork_count_when_share_all(self):
        ShareLinkFactory(user=self.user, share_type='mixed', is_share_all=True)

        response = self.client.get('/api/artwork/manage_share_links/')

        result = response.data['results'][0]
        self.assertEqual(result['artwork_count'], 2)

    def test_recipients_count(self):
        link = ShareLinkFactory(user=self.user, share_type='mixed', recipient_type='specific')
        r1 = UserFactory()
        r2 = UserFactory()
        link.recipients.add(r1, r2)

        response = self.client.get('/api/artwork/manage_share_links/')

        result = response.data['results'][0]
        self.assertEqual(result['recipients_count'], 2)

    def test_status_active(self):
        ShareLinkFactory(user=self.user, share_type='mixed', is_active=True, expiration_type='never')

        response = self.client.get('/api/artwork/manage_share_links/')

        result = response.data['results'][0]
        self.assertEqual(result['status'], 'active')

    def test_status_inactive(self):
        ShareLinkFactory(user=self.user, share_type='mixed', is_active=False)

        response = self.client.get('/api/artwork/manage_share_links/?is_active=false')

        result = response.data['results'][0]
        self.assertEqual(result['status'], 'inactive')

    def test_status_expired(self):
        ShareLinkFactory(
            user=self.user,
            share_type='mixed',
            is_active=True,
            expiration_type='custom',
            expires_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.get('/api/artwork/manage_share_links/')

        result = response.data['results'][0]
        self.assertEqual(result['status'], 'expired')


class RevokeShareLinkAPIViewTest(BaseUserTest):
    """Tests for RevokeShareLinkAPIView."""

    def test_revoke_share_link_success(self):
        link = ShareLinkFactory(user=self.user)

        response = self.client.delete(f'/api/artwork/manage_share_links/{link.id}/revoke/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Share link revoked successfully.')
        self.assertFalse(ShareLink.objects.filter(id=link.id).exists())

    def test_revoke_share_link_not_found(self):
        import uuid
        fake_id = uuid.uuid4()

        response = self.client.delete(f'/api/artwork/manage_share_links/{fake_id}/revoke/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Share link not found.')

    def test_revoke_share_link_of_other_user_not_found(self):
        other_user = UserFactory()
        link = ShareLinkFactory(user=other_user)

        response = self.client.delete(f'/api/artwork/manage_share_links/{link.id}/revoke/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ExtendShareLinkAPIViewTest(BaseUserTest):
    """Tests for ExtendShareLinkAPIView."""

    def test_extend_share_link_with_permanent(self):
        link = ShareLinkFactory(
            user=self.user,
            expiration_type='custom',
            expires_at=timezone.now() - timedelta(days=1),
            is_active=False,
        )

        response = self.client.patch(
            f'/api/artwork/manage_share_links/{link.id}/extend/',
            data={'expiration_type': 'permanent'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Share link extended successfully.')
        link.refresh_from_db()
        self.assertEqual(link.expiration_type, 'permanent')
        self.assertIsNone(link.expires_at)
        self.assertTrue(link.is_active)

    def test_extend_share_link_with_never(self):
        link = ShareLinkFactory(
            user=self.user,
            expiration_type='custom',
            expires_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.patch(
            f'/api/artwork/manage_share_links/{link.id}/extend/',
            data={'expiration_type': 'never'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        link.refresh_from_db()
        self.assertIsNone(link.expires_at)

    def test_extend_share_link_with_custom_date(self):
        link = ShareLinkFactory(user=self.user, expiration_type='never')
        future_date = (timezone.now() + timedelta(days=30)).isoformat()

        response = self.client.patch(
            f'/api/artwork/manage_share_links/{link.id}/extend/',
            data={'expiration_type': 'custom', 'expires_at': future_date},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        link.refresh_from_db()
        self.assertEqual(link.expiration_type, 'custom')
        self.assertIsNotNone(link.expires_at)

    def test_extend_share_link_custom_without_date_fails(self):
        link = ShareLinkFactory(user=self.user)

        response = self.client.patch(
            f'/api/artwork/manage_share_links/{link.id}/extend/',
            data={'expiration_type': 'custom'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_extend_share_link_custom_with_past_date_fails(self):
        link = ShareLinkFactory(user=self.user)
        past_date = (timezone.now() - timedelta(days=1)).isoformat()

        response = self.client.patch(
            f'/api/artwork/manage_share_links/{link.id}/extend/',
            data={'expiration_type': 'custom', 'expires_at': past_date},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_extend_share_link_not_found(self):
        import uuid
        fake_id = uuid.uuid4()

        response = self.client.patch(
            f'/api/artwork/manage_share_links/{fake_id}/extend/',
            data={'expiration_type': 'never'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Share link not found.')

    def test_extend_share_link_of_other_user_not_found(self):
        other_user = UserFactory()
        link = ShareLinkFactory(user=other_user)

        response = self.client.patch(
            f'/api/artwork/manage_share_links/{link.id}/extend/',
            data={'expiration_type': 'never'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
