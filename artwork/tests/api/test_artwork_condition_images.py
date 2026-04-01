from django.utils import timezone
from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.condition_image_batch import (
    ConditionImageBatchFactory,
    ConditionImageFactory,
)
from core.accounts.tests.api.base_user_test import BaseUserTest


class ArtworkConditionImagesApiTests(BaseUserTest):

    def setUp(self) -> None:
        super().setUp()

        self.artwork = ArtworkFactory()

        self.batch1 = ConditionImageBatchFactory(
            artwork=self.artwork,
            created_at=timezone.now() - timezone.timedelta(days=2),
        )
        self.image1_batch1 = ConditionImageFactory(batch=self.batch1, order=1)
        self.image2_batch1 = ConditionImageFactory(batch=self.batch1, order=2)

        self.batch2 = ConditionImageBatchFactory(
            artwork=self.artwork,
            created_at=timezone.now() - timezone.timedelta(days=1),
        )
        self.image1_batch2 = ConditionImageFactory(batch=self.batch2, order=1)

        self.other_artwork = ArtworkFactory()
        self.other_batch = ConditionImageBatchFactory(artwork=self.other_artwork)
        self.other_image = ConditionImageFactory(batch=self.other_batch)

    def test_list_condition_images_success(self):
        response = self.client.get(
            f'/api/artwork/artwork/{self.artwork.id}/condition_images/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_ordering_by_batch_created_at(self):
        response = self.client.get(
            f'/api/artwork/artwork/{self.artwork.id}/condition_images/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data[0]['id'], self.image1_batch1.id)
        self.assertEqual(response.data[1]['id'], self.image2_batch1.id)
        self.assertEqual(response.data[2]['id'], self.image1_batch2.id)

    def test_artwork_not_found(self):
        non_existent_id = 999999
        response = self.client.get(
            f'/api/artwork/artwork/{non_existent_id}/condition_images/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_structure(self):
        response = self.client.get(
            f'/api/artwork/artwork/{self.artwork.id}/condition_images/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

        first_item = response.data[0]
        self.assertIn('id', first_item)
        self.assertIn('owner', first_item)
        self.assertIn('created_at', first_item)
        self.assertIn('image', first_item)

        self.assertIsInstance(first_item['owner'], dict)
        self.assertIn('id', first_item['owner'])

        expected_created_at = self.batch1.created_at.isoformat().replace('+00:00', 'Z')
        self.assertEqual(first_item['created_at'], expected_created_at)

    def test_empty_list_when_no_condition_images(self):
        artwork_without_images = ArtworkFactory()

        response = self.client.get(
            f'/api/artwork/artwork/{artwork_without_images.id}/condition_images/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
