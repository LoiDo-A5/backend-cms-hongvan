from __future__ import annotations

import base64
import logging
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import ImagePhotobooth, PaymentOrder

logger = logging.getLogger(__name__)


class _ImageItemSerializer(serializers.Serializer):
    image_base64 = serializers.CharField()
    round_index = serializers.IntegerField(min_value=0, default=0)
    photo_index = serializers.IntegerField(min_value=0, default=0)


class SaveImagesSerializer(serializers.Serializer):
    """Payload: order identifier + array of images."""
    order_id = serializers.CharField(
        max_length=100,
        help_text='txn_ref of the PaymentOrder',
    )
    images = _ImageItemSerializer(many=True)


class SaveImagesView(APIView):
    """
    POST /api/photobooth/save-images/

    Nhận danh sách ảnh (base64) + order_id, lưu file ảnh vào ImagePhotobooth
    và gắn với PaymentOrder tương ứng.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        ser = SaveImagesSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        order_id = ser.validated_data['order_id'].strip()
        images_data = ser.validated_data['images']

        if not images_data:
            return Response(
                {'detail': 'Không có ảnh nào để lưu.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = PaymentOrder.objects.filter(txn_ref=order_id).first()
        if not order:
            return Response(
                {'detail': f'Không tìm thấy đơn thanh toán "{order_id}".'},
                status=status.HTTP_404_NOT_FOUND,
            )

        saved = []
        for item in images_data:
            raw_b64 = item['image_base64']
            round_idx = item.get('round_index', 0)
            photo_idx = item.get('photo_index', 0)

            image_bytes = self._decode_base64(raw_b64)

            filename = f'{order.txn_ref}_{round_idx}_{photo_idx}_{uuid.uuid4().hex[:8]}.jpg'
            img_obj = ImagePhotobooth(
                payment_order=order,
                round_index=round_idx,
                photo_index=photo_idx,
            )
            img_obj.image.save(filename, ContentFile(image_bytes), save=True)
            saved.append({
                'id': img_obj.id,
                'round_index': img_obj.round_index,
                'photo_index': img_obj.photo_index,
                'image_url': img_obj.image.url,
            })

        return Response(
            {'saved_count': len(saved), 'images': saved},
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _decode_base64(raw: str) -> bytes:
        if ',' in raw and raw.startswith('data:'):
            raw = raw.split(',', 1)[1]
        return base64.b64decode(raw)
