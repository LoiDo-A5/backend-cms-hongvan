from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.size_artwork import SizeArtworkFactory
from activity_log.models.artwork_log import ArtworkLog, ACTION_UPDATE_ARTWORK
from core.accounts.tests.api.base_user_test import BaseUserTest


class ActivityLogUpdateTest(BaseUserTest):
    def test_update_artwork_creates_activity_log_for_title_change(self):
        artwork = ArtworkFactory(owner=self.user, status='available', title='Old Title', inventory_code='INV-001')

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'title': 'New Title',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        logs = ArtworkLog.objects.filter(artwork_id=artwork.id).order_by('-id')
        self.assertTrue(logs.exists())

        log = logs.first()

        self.assertEqual(log.action_type, ACTION_UPDATE_ARTWORK)
        expected_template_en = ('Changed {field} of artwork {title} (inventory code: {inventory_code}) '
                                'from {old} to {new}')
        expected_template_vi = ('Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) '
                                'từ {old} thành {new}')
        expected_params = {
            'field': 'title',
            'title': 'New Title',
            'inventory_code': 'INV-001',
            'old': 'Old Title',
            'new': 'New Title',
        }
        expected_content_en = expected_template_en.format(**expected_params)
        expected_content_vi = expected_template_vi.format(**expected_params)

        self.assertEqual(log.template_en, expected_template_en)
        self.assertEqual(log.template_vi, expected_template_vi)
        self.assertEqual(log.content_en, expected_content_en)
        self.assertEqual(log.content_vi, expected_content_vi)
        self.assertEqual(log.params, expected_params)

    def test_update_artwork_size_from_none_creates_activity_log(self):
        size = SizeArtworkFactory(length=None, width=None, depth=None, weight=None)
        artwork = ArtworkFactory(
            owner=self.user,
            status='available',
            title='Sizeless Artwork',
            inventory_code='INV-002',
            size=size,
        )

        payload = {
            'size': {
                'width': 30,
                'height': 40,
            },
        }

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            payload,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        logs = ArtworkLog.objects.filter(artwork_id=artwork.id).order_by('-id')
        self.assertTrue(logs.exists())

        log = logs.first()
        self.assertEqual(log.action_type, ACTION_UPDATE_ARTWORK)

        expected_template_en = ('Changed {field} of artwork {title} (inventory code: {inventory_code}) '
                                'from {old} to {new}')
        expected_template_vi = ('Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) '
                                'từ {old} thành {new}')
        expected_params = {
            'field': 'size',
            'title': 'Sizeless Artwork',
            'inventory_code': 'INV-002',
            'old': 'N/A',
            'new': 'W:30.00 x H:40.00',
        }

        self.assertEqual(log.template_en, expected_template_en)
        self.assertEqual(log.template_vi, expected_template_vi)
        self.assertEqual(log.content_en, expected_template_en.format(**expected_params))
        self.assertEqual(log.content_vi, expected_template_vi.format(**expected_params))
        self.assertEqual(log.params, expected_params)

    def test_update_artwork_size_activity_log(self):
        size = SizeArtworkFactory(length=None, width=1, depth=None, weight=None)
        artwork = ArtworkFactory(
            owner=self.user,
            status='available',
            title='Sizeless Artwork',
            inventory_code='INV-002',
            size=size,
        )

        payload = {
            'size': {
                'width': 30,
                'height': 40,
            },
        }

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            payload,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        logs = ArtworkLog.objects.filter(artwork_id=artwork.id).order_by('-id')
        self.assertTrue(logs.exists())

        log = logs.first()
        self.assertEqual(log.action_type, ACTION_UPDATE_ARTWORK)

        expected_template_en = ('Changed {field} of artwork {title} (inventory code: {inventory_code}) '
                                'from {old} to {new}')
        expected_template_vi = ('Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) '
                                'từ {old} thành {new}')
        expected_params = {
            'field': 'size',
            'title': 'Sizeless Artwork',
            'inventory_code': 'INV-002',
            'old': 'W:1.00',
            'new': 'W:30.00 x H:40.00',
        }

        self.assertEqual(log.template_en, expected_template_en)
        self.assertEqual(log.template_vi, expected_template_vi)
        self.assertEqual(log.content_en, expected_template_en.format(**expected_params))
        self.assertEqual(log.content_vi, expected_template_vi.format(**expected_params))
        self.assertEqual(log.params, expected_params)
