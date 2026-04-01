from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PhotoboothDevice
from core.photobooth.serializers.capture_options import (
    PhotoboothBackgroundOptionSerializer,
    PhotoboothFilterOptionSerializer,
)


class CaptureOptionsView(APIView):
    """
    GET /api/photobooth/capture-options/?device_id=<id>
    Trả về filters và backgrounds đã gán cho PhotoboothDevice (chỉ is_active).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        device_id = (request.query_params.get('device_id') or '').strip()
        if not device_id:
            return Response(
                {'detail': 'Thiếu tham số device_id.', 'filters': [], 'backgrounds': []},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device = PhotoboothDevice.objects.filter(device_id=device_id).first()
        if not device:
            return Response(
                {
                    'detail': 'Thiết bị chưa có trên hệ thống.',
                    'registered': False,
                    'filters': [],
                    'backgrounds': [],
                },
                status=status.HTTP_200_OK,
            )

        filters_qs = device.filters.filter(is_active=True).order_by('sort_order', 'id')
        backgrounds_qs = device.backgrounds.filter(is_active=True).order_by('sort_order', 'id')

        ctx = {'request': request}
        return Response(
            {
                'registered': True,
                'device': {'id': device.id, 'name': device.name, 'device_id': device.device_id},
                'filters': PhotoboothFilterOptionSerializer(
                    filters_qs, many=True, context=ctx
                ).data,
                'backgrounds': PhotoboothBackgroundOptionSerializer(
                    backgrounds_qs, many=True, context=ctx
                ).data,
            },
            status=status.HTTP_200_OK,
        )
