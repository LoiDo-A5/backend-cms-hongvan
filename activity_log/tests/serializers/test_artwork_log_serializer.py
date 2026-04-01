from activity_log.serializers.artwork_log import ArtworkLogSerializer
from activity_log.models import ArtworkLog
from artwork.factories.artwork import ArtworkFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ArtworkLogSerializerTest(BaseUserTest):
    def test_formatted_timestamp_is_none_when_created_at_missing(self):
        artwork = ArtworkFactory(owner=self.user, title='T1')
        log = ArtworkLog(
            artwork=artwork,
            user=self.user,
            action_type='update_title',
            content_en='desc',
        )
        ser = ArtworkLogSerializer(instance=log)
        data = ser.data
        self.assertIsNone(data['formatted_timestamp'])

    def test_formatted_timestamp_is_formatted_when_created_at_present(self):
        artwork = ArtworkFactory(owner=self.user, title='T2')
        log = ArtworkLog.objects.create(
            artwork=artwork,
            user=self.user,
            action_type='update_title',
            content_en='desc',
        )
        ser = ArtworkLogSerializer(instance=log)
        data = ser.data
        self.assertEqual(data['formatted_timestamp'], log.created_at.strftime('%d %b %Y %H:%M:%S'))
