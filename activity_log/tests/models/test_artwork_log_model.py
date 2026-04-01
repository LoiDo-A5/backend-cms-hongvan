from activity_log.models import ArtworkLog
from artwork.factories.artwork import ArtworkFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ArtworkLogModelStrTest(BaseUserTest):
    def test_str_with_deleted_artwork(self):
        log = ArtworkLog.objects.create(
            artwork=None,
            user=self.user,
            action_type='update_title',
            content_en='deleted artwork log',
        )
        s = str(log)
        self.assertIn('Deleted Artwork', s)
        self.assertIn('update_title', s)

    def test_str_with_artwork_without_title(self):
        artwork = ArtworkFactory(owner=self.user, title='')
        log = ArtworkLog.objects.create(
            artwork=artwork,
            user=self.user,
            action_type='update_description',
            content_en='no title',
        )
        s = str(log)
        self.assertIn(f'Artwork #{artwork.pk}', s)
        self.assertIn('update_description', s)
