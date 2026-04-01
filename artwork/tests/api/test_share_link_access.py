from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.share_link import ShareLinkFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ShareLinkAccessAPIViewGetTests(BaseUserTest):

    def setUp(self) -> None:
        super().setUp()
        self.artwork = ArtworkFactory(owner=self.user, is_public=True)
        self.share_link = ShareLinkFactory(
            user=self.user,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=True,
        )

    def test_get_public_share_link_without_password_success(self):
        response = self.client.get(f'/api/artwork/share/{self.share_link.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('share_link', response.data)
        self.assertEqual(response.data['share_link']['id'], str(self.share_link.id))

    def test_get_share_link_not_found_returns_404(self):

        response = self.client.get('/api/artwork/share/xxx/', format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_inactive_share_link_returns_403(self):
        inactive_link = ShareLinkFactory(
            user=self.user,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=False,
        )
        response = self.client.get(f'/api/artwork/share/{inactive_link.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'This share link is no longer valid')

    def test_get_share_link_with_password_without_providing_password_returns_401(self):
        password_link = ShareLinkFactory(
            user=self.user,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=True,
            password='secret123',
        )
        response = self.client.get(f'/api/artwork/share/{password_link.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertTrue(response.data.get('requires_password'))

    def test_get_share_link_with_password_with_wrong_password_returns_401(self):
        password_link = ShareLinkFactory(
            user=self.user,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=True,
            password='secret123',
        )
        response = self.client.get(
            f'/api/artwork/share/{password_link.id}/?password=wrongpassword',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_get_share_link_with_password_with_correct_password_success(self):
        password_link = ShareLinkFactory(
            user=self.user,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=True,
            password='secret123',
        )
        response = self.client.get(
            f'/api/artwork/share/{password_link.id}/?password=secret123',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('share_link', response.data)

    def test_get_share_link_specific_recipient_unauthenticated_returns_401(self):
        recipient_link = ShareLinkFactory(
            user=self.user,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=True,
            recipient_type='specific',
        )
        self.client.logout()
        response = self.client.get(f'/api/artwork/share/{recipient_link.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertTrue(response.data.get('requires_login'))

    def test_get_share_link_specific_recipient_not_in_list_returns_403(self):
        other_user = UserFactory()
        user_1 = UserFactory()
        recipient_link = ShareLinkFactory(
            user=user_1,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=True,
            recipient_type='specific',
        )
        recipient_link.recipients.add(other_user)

        response = self.client.get(f'/api/artwork/share/{recipient_link.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this share link')

    def test_get_share_link_specific_recipient_in_list_success(self):
        user = UserFactory()
        recipient_link = ShareLinkFactory(
            user=user,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=True,
            recipient_type='specific',
        )
        recipient_link.recipients.add(self.user)
        response = self.client.get(f'/api/artwork/share/{recipient_link.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('share_link', response.data)

    def test_get_share_link_owner_can_access_specific_recipient_link(self):
        other_user = UserFactory()
        recipient_link = ShareLinkFactory(
            user=self.user,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=True,
            recipient_type='specific',
        )
        recipient_link.recipients.add(other_user)

        response = self.client.get(f'/api/artwork/share/{recipient_link.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('share_link', response.data)


class ShareLinkAccessAPIViewPostTests(BaseUserTest):

    def setUp(self) -> None:
        super().setUp()
        self.artwork = ArtworkFactory(owner=self.user, is_public=True)
        self.share_link_with_password = ShareLinkFactory(
            user=self.user,
            shared_items=[{'id': self.artwork.id, 'type': 'artwork'}],
            is_active=True,
            password='secret123',
        )

    def test_post_share_link_with_correct_password_success(self):
        data = {'password': 'secret123'}
        response = self.client.post(
            f'/api/artwork/share/{self.share_link_with_password.id}/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('share_link', response.data)

    def test_post_share_link_with_wrong_password_returns_401(self):
        data = {'password': 'wrongpassword'}
        response = self.client.post(
            f'/api/artwork/share/{self.share_link_with_password.id}/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_post_share_link_without_password_field_returns_400(self):
        data = {}
        response = self.client.post(
            f'/api/artwork/share/{self.share_link_with_password.id}/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'password': ['This field is required.']})
