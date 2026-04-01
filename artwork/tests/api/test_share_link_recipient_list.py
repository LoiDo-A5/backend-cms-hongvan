from rest_framework import status

from artwork.factories.share_link import ShareLinkFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ShareLinkRecipientListViewTest(BaseUserTest):

    def setUp(self) -> None:
        super().setUp()
        self.recipient_user_1 = UserFactory()
        self.recipient_user_2 = UserFactory()
        self.recipient_user_3 = UserFactory()

    def test_get_recipients_list_success(self):
        share_link_1 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='mixed')
        share_link_1.recipients.add(self.recipient_user_1, self.recipient_user_2)

        share_link_2 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='mixed')
        share_link_2.recipients.add(self.recipient_user_2, self.recipient_user_3)

        response = self.client.get(f'/api/artwork/share_link/user/{self.user.id}/recipient/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 3)

        recipient_ids = [recipient['id'] for recipient in results]
        self.assertIn(self.recipient_user_1.id, recipient_ids)
        self.assertIn(self.recipient_user_2.id, recipient_ids)
        self.assertIn(self.recipient_user_3.id, recipient_ids)

    def test_get_recipients_list_no_duplicates(self):
        share_link_1 = ShareLinkFactory(user=self.user, recipient_type='specific')
        share_link_1.recipients.add(self.recipient_user_1)

        share_link_2 = ShareLinkFactory(user=self.user, recipient_type='specific')
        share_link_2.recipients.add(self.recipient_user_1)

        share_link_3 = ShareLinkFactory(user=self.user, recipient_type='specific')
        share_link_3.recipients.add(self.recipient_user_1)

        response = self.client.get(f'/api/artwork/share_link/user/{self.user.id}/recipient/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.recipient_user_1.id)

    def test_get_recipients_list_empty_when_no_share_links(self):
        other_user = UserFactory()

        response = self.client.get(f'/api/artwork/share_link/user/{other_user.id}/recipient/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 0)

    def test_get_recipients_list_requires_authentication(self):
        self.client.logout()

        response = self.client.get(f'/api/artwork/share_link/user/{self.user.id}/recipient/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_recipient_removes_recipient_from_all_mixed_share_links(self):
        share_link_1 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='mixed')
        share_link_1.recipients.add(self.recipient_user_1, self.recipient_user_2)

        share_link_2 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='mixed')
        share_link_2.recipients.add(self.recipient_user_1)

        share_link_3 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='artwork')
        share_link_3.recipients.add(self.recipient_user_1)

        response = self.client.delete(
            f'/api/artwork/share_link/user/{self.user.id}/recipient/{self.recipient_user_1.id}/',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data.get('removed_from_share_links'), 2)

        share_link_1.refresh_from_db()
        share_link_2.refresh_from_db()
        share_link_3.refresh_from_db()

        self.assertFalse(share_link_1.recipients.filter(id=self.recipient_user_1.id).exists())
        self.assertFalse(share_link_2.recipients.filter(id=self.recipient_user_1.id).exists())

    def test_delete_recipient_returns_zero_when_recipient_not_in_mixed_share_links(self):
        share_link_1 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='mixed')
        share_link_1.recipients.add(self.recipient_user_2)

        share_link_2 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='artwork')
        share_link_2.recipients.add(self.recipient_user_1)

        response = self.client.delete(
            f'/api/artwork/share_link/user/{self.user.id}/recipient/{self.recipient_user_1.id}/',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data.get('removed_from_share_links'), 0)

        share_link_1.refresh_from_db()
        share_link_2.refresh_from_db()

        self.assertTrue(share_link_1.recipients.filter(id=self.recipient_user_2.id).exists())
        self.assertTrue(share_link_2.recipients.filter(id=self.recipient_user_1.id).exists())

    def test_delete_recipient_forbidden_when_owner_mismatch(self):
        other_user = UserFactory()

        share_link = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='mixed')
        share_link.recipients.add(self.recipient_user_1)

        response = self.client.delete(
            f'/api/artwork/share_link/user/{other_user.id}/recipient/{self.recipient_user_1.id}/',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        share_link.refresh_from_db()
        self.assertTrue(share_link.recipients.filter(id=self.recipient_user_1.id).exists())


class ShareLinkRecipientArtworkRemoveViewTest(BaseUserTest):

    def setUp(self) -> None:
        super().setUp()
        self.recipient_user_1 = UserFactory()
        self.recipient_user_2 = UserFactory()

    def test_delete_recipient_type_artwork_removes_recipient_from_all_artwork_share_links(self):
        share_link_1 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='artwork')
        share_link_1.recipients.add(self.recipient_user_1, self.recipient_user_2)

        share_link_2 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='artwork')
        share_link_2.recipients.add(self.recipient_user_1)

        share_link_3 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='mixed')
        share_link_3.recipients.add(self.recipient_user_1)

        response = self.client.delete(
            f'/api/artwork/share_link/user/{self.user.id}/recipient_type_artwork/{self.recipient_user_1.id}/',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data.get('removed_from_share_links'), 2)

        share_link_1.refresh_from_db()
        share_link_2.refresh_from_db()
        share_link_3.refresh_from_db()

        self.assertFalse(share_link_1.recipients.filter(id=self.recipient_user_1.id).exists())
        self.assertTrue(share_link_1.recipients.filter(id=self.recipient_user_2.id).exists())
        self.assertFalse(share_link_2.recipients.filter(id=self.recipient_user_1.id).exists())
        self.assertTrue(share_link_3.recipients.filter(id=self.recipient_user_1.id).exists())

    def test_delete_recipient_type_artwork_forbidden_when_owner_mismatch(self):
        other_user = UserFactory()

        share_link = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='artwork')
        share_link.recipients.add(self.recipient_user_1)

        response = self.client.delete(
            f'/api/artwork/share_link/user/{other_user.id}/recipient_type_artwork/{self.recipient_user_1.id}/',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        share_link.refresh_from_db()
        self.assertTrue(share_link.recipients.filter(id=self.recipient_user_1.id).exists())

    def test_delete_recipient_type_artwork_requires_authentication(self):
        self.client.logout()

        response = self.client.delete(
            f'/api/artwork/share_link/user/{self.user.id}/recipient_type_artwork/{self.recipient_user_1.id}/',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ShareLinkRecipientArtworkListViewTest(BaseUserTest):

    def setUp(self) -> None:
        super().setUp()
        self.recipient_user_1 = UserFactory()
        self.recipient_user_2 = UserFactory()

    def test_get_recipients_list_type_artwork_success(self):
        share_link_1 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='artwork')
        share_link_1.recipients.add(self.recipient_user_1)

        share_link_2 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='artwork')
        share_link_2.recipients.add(self.recipient_user_2)

        share_link_3 = ShareLinkFactory(user=self.user, recipient_type='specific', share_type='mixed')
        share_link_3.recipients.add(self.recipient_user_1, self.recipient_user_2)

        response = self.client.get(
            f'/api/artwork/share_link/user/{self.user.id}/recipient_type_artwork/',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)

        recipient_ids = [recipient['id'] for recipient in results]
        self.assertIn(self.recipient_user_1.id, recipient_ids)
        self.assertIn(self.recipient_user_2.id, recipient_ids)

    def test_get_recipients_list_type_artwork_requires_authentication(self):
        self.client.logout()

        response = self.client.get(
            f'/api/artwork/share_link/user/{self.user.id}/recipient_type_artwork/',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
