from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.models.condition_image_batch import ConditionImageBatch
from artwork.models.condition_image_batch_log import ConditionImageBatchLog
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


class ArtworkLessUpdateConditionImagesTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.ARTIST
        self.user.save(update_fields=['role'])

    def test_partial_update_condition_images_creates_snapshot_log(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save(update_fields=['role'])
        artwork = ArtworkFactory(owner=self.user)
        edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=edition)
        url = f'/api/artwork/artwork/{artwork.uuid}/'

        payload = {
            'condition_images': [
                'cond_1.png',
                'cond_2.png',
            ],
        }
        response = self.client.patch(url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        batch = ConditionImageBatch.objects.filter(artwork_id=artwork.id, owner_id=self.user.id).first()
        self.assertIsNotNone(batch)
        self.assertEqual(ConditionImageBatchLog.objects.filter(batch=batch, artwork=artwork).count(), 1)

        log = ConditionImageBatchLog.objects.filter(batch=batch, artwork=artwork).first()
        self.assertEqual(log.images_snapshot, ['cond_1.png', 'cond_2.png'])

    def test_partial_update_condition_images_creates_snapshot_log_twice(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save(update_fields=['role'])
        artwork = ArtworkFactory(owner=self.user)
        edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=edition)
        url = f'/api/artwork/artwork/{artwork.uuid}/'

        first_payload = {
            'condition_images': [
                'img_a.png',
                'img_b.png',
            ],
        }
        r1 = self.client.patch(url, data=first_payload, format='json')
        self.assertEqual(r1.status_code, status.HTTP_200_OK)

        second_payload = {
            'condition_images': [
                'img_c.png',
            ],
        }
        r2 = self.client.patch(url, data=second_payload, format='json')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

        batch = ConditionImageBatch.objects.filter(artwork_id=artwork.id, owner_id=self.user.id).first()
        self.assertIsNotNone(batch)
        self.assertEqual(ConditionImageBatchLog.objects.filter(batch=batch, artwork=artwork).count(), 2)

        latest_log = ConditionImageBatchLog.objects.filter(batch=batch, artwork=artwork).order_by('-id').first()
        self.assertEqual(latest_log.images_snapshot, ['img_c.png'])
