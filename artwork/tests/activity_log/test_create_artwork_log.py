from activity_log.models.artwork_log import ArtworkLog, ACTION_ARTWORK_UPLOADED
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.tests.utils.artwork import create_data
from rest_framework import status


class ActivityLogCreateTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.ARTIST
        self.user.save()

    def test_create_artwork_creates_upload_log(self):
        data = create_data(user_id=self.user.id, inventory_code='INV-123', title='New Piece')

        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        log = (
            ArtworkLog.objects.filter(artwork_id=response.data['id'], action_type=ACTION_ARTWORK_UPLOADED,
                                      user_id=self.user.id)
            .order_by('-id')
            .first()
        )
        self.assertIsNotNone(log)

        expected_template_en = 'Successfully uploaded artwork {title} (inventory code: {inventory_code})'
        expected_template_vi = 'Tải lên tác phẩm thành công {title} (mã kiểm kê: {inventory_code})'
        expected_params = {
            'title': 'New Piece',
            'inventory_code': 'INV-123',
        }

        self.assertEqual(log.action_type, ACTION_ARTWORK_UPLOADED)
        self.assertEqual(log.template_en, expected_template_en)
        self.assertEqual(log.template_vi, expected_template_vi)
        self.assertEqual(log.content_en, expected_template_en.format(**expected_params))
        self.assertEqual(log.content_vi, expected_template_vi.format(**expected_params))
        self.assertEqual(log.params, expected_params)

    def test_create_artwork_log_handles_missing_fields(self):
        data = create_data(user_id=self.user.id, inventory_code=None, title='New Piece')
        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        log = (
            ArtworkLog.objects.filter(artwork_id=response.data['id'],
                                      action_type=ACTION_ARTWORK_UPLOADED, user_id=self.user.id)
            .order_by('-id')
            .first()
        )
        self.assertIsNotNone(log)

        expected_template_en = 'Successfully uploaded artwork {title} (inventory code: {inventory_code})'
        expected_template_vi = 'Tải lên tác phẩm thành công {title} (mã kiểm kê: {inventory_code})'
        expected_params = {
            'title': 'New Piece',
            'inventory_code': 'N/A',
        }

        self.assertEqual(log.action_type, ACTION_ARTWORK_UPLOADED)
        self.assertEqual(log.template_en, expected_template_en)
        self.assertEqual(log.template_vi, expected_template_vi)
        self.assertEqual(log.content_en, expected_template_en.format(**expected_params))
        self.assertEqual(log.content_vi, expected_template_vi.format(**expected_params))
        self.assertEqual(log.params, expected_params)
