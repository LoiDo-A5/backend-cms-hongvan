from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PhotoboothDevice


class PhotoboothDeviceRegisterView(APIView):
    """
    POST /api/photobooth/devices/register/
    Đăng ký / cập nhật thiết bị khi mở màn hình chào: tạo bản ghi nếu chưa có device_id.

    Body: { "device_id": "<uuid>", "name": "<tùy chọn>" }
    - name rỗng → dùng PHOTOBOOTH_DEVICE_DEFAULT_NAME (mặc định \"Photobooth\").
    - Thiết bị đã tồn tại: cập nhật last_seen_at; nếu gửi name thì đồng bộ tên.
    - is_active=False → 403.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        device_id = (request.data.get('device_id') or '').strip()
        name = (request.data.get('name') or '').strip()

        if not device_id:
            return Response(
                {'detail': 'Thiếu device_id.', 'code': 'missing_device_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(device_id) > 128:
            return Response(
                {'detail': 'device_id quá dài.', 'code': 'invalid_device_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        default_name = (
            getattr(settings, 'PHOTOBOOTH_DEVICE_DEFAULT_NAME', None) or 'Photobooth'
        ).strip() or 'Photobooth'
        display_name = name if name else default_name

        now = timezone.now()

        dev, created = PhotoboothDevice.objects.get_or_create(
            device_id=device_id,
            defaults={
                'name': display_name,
                'is_active': True,
                'last_seen_at': now,
            },
        )

        if not created:
            if not dev.is_active:
                return Response(
                    {'detail': 'Thiết bị đã bị vô hiệu hóa.', 'code': 'inactive'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            upd: dict = {'last_seen_at': now}
            if name:
                upd['name'] = name
            PhotoboothDevice.objects.filter(pk=dev.pk).update(**upd)
            dev.refresh_from_db()

        return Response(
            {
                'ok': True,
                'created': created,
                'device': {
                    'id': dev.id,
                    'device_id': dev.device_id,
                    'name': dev.name,
                },
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
