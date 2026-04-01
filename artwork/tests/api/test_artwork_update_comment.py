from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.models.comment_artwork import CommentArtwork


class ArtworkUpdateCommentApiTest(BaseUserTest):
    def _url(self, artwork_id: int) -> str:
        return f'/api/artwork/artwork/{artwork_id}/'

    def test_create_new_comment_when_no_id(self):
        artwork = ArtworkFactory(owner=self.user)

        payload = {
            'comment': {
                'content': 'New comment from owner',
            },
        }

        res = self.client.patch(self._url(artwork.uuid), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(CommentArtwork.objects.filter(artwork=artwork, user=self.user).count(), 1)
        c = CommentArtwork.objects.get(artwork=artwork, user=self.user)
        self.assertEqual(c.content, 'New comment from owner')
        self.assertFalse(c.is_hidden)

    def test_update_existing_comment_content_by_owner(self):
        artwork = ArtworkFactory(owner=self.user)
        c = CommentArtwork.objects.create(artwork=artwork, user=self.user, content='Old')

        payload = {
            'comment': {
                'id': c.id,
                'content': 'Updated content',
            },
        }

        res = self.client.patch(self._url(artwork.uuid), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        c.refresh_from_db()
        self.assertEqual(c.content, 'Updated content')

    def test_update_existing_comment_content_wrong_user_should_404(self):
        artwork = ArtworkFactory(owner=self.user)
        other_user = UserFactory()
        c = CommentArtwork.objects.create(artwork=artwork, user=other_user, content="Other's comment")

        payload = {
            'comment': {
                'id': c.id,
                'content': 'Attempted overwrite',
            },
        }

        res = self.client.patch(self._url(artwork.uuid), payload, format='json')

        # get_object_or_404 inside serializer should raise 404 when user does not own the comment
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        c.refresh_from_db()
        self.assertEqual(c.content, "Other's comment")

    def test_visibility_updates_toggle_values(self):
        artwork = ArtworkFactory(owner=self.user)
        # Comments may be from any users but must belong to the same artwork
        c1 = CommentArtwork.objects.create(artwork=artwork, user=self.user, content='A', is_hidden=False)
        other_user = UserFactory()
        c2 = CommentArtwork.objects.create(artwork=artwork, user=other_user, content='B', is_hidden=True)

        payload = {
            'comment': {
                'visibility_updates': [
                    {'id': c1.id, 'is_hidden': True},   # change False -> True
                    {'id': c2.id, 'is_hidden': False},  # change True -> False
                ],
            },
        }

        res = self.client.patch(self._url(artwork.uuid), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        c1.refresh_from_db()
        c2.refresh_from_db()
        self.assertTrue(c1.is_hidden)
        self.assertFalse(c2.is_hidden)

    def test_visibility_updates_skip_when_missing_fields(self):
        artwork = ArtworkFactory(owner=self.user)
        c1 = CommentArtwork.objects.create(artwork=artwork, user=self.user, content='A', is_hidden=False)
        c2 = CommentArtwork.objects.create(artwork=artwork, user=self.user, content='B', is_hidden=True)

        payload = {
            'comment': {
                'visibility_updates': [
                    {'id': c1.id},                  # missing is_hidden -> skip
                    {'is_hidden': False},           # missing id -> skip
                    {'id': c2.id, 'is_hidden': None},  # None -> skip
                ],
            },
        }

        res = self.client.patch(self._url(artwork.uuid), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        c1.refresh_from_db()
        c2.refresh_from_db()
        self.assertFalse(c1.is_hidden)
        self.assertTrue(c2.is_hidden)

    def test_visibility_update_no_change_when_same_value(self):
        artwork = ArtworkFactory(owner=self.user)
        c1 = CommentArtwork.objects.create(artwork=artwork, user=self.user, content='A', is_hidden=False)

        payload = {
            'comment': {
                'visibility_updates': [
                    {'id': c1.id, 'is_hidden': False},  # already False, no-op
                ],
            },
        }

        res = self.client.patch(self._url(artwork.uuid), payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        c1.refresh_from_db()
        self.assertFalse(c1.is_hidden)

    def test_comment_block_ignored_when_comment_is_null(self):
        artwork = ArtworkFactory(owner=self.user)
        # When "comment" is omitted or is null, nothing should happen and request should succeed
        payload = {
            # no comment key
        }
        res = self.client.patch(self._url(artwork.uuid), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(CommentArtwork.objects.filter(artwork=artwork).count(), 0)

        payload2 = {'comment': None}
        res2 = self.client.patch(self._url(artwork.uuid), payload2, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(CommentArtwork.objects.filter(artwork=artwork).count(), 0)
