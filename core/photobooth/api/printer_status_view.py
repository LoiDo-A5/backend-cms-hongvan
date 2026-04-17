from __future__ import annotations

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PhotoboothDevice


class PrinterStatusUpdateView(APIView):
    """
    POST /api/photobooth/devices/printer-status/
    Electron app gửi trạng thái máy in định kỳ.

    Body: {
        "device_id": "<uuid>",
        "printer_name": "Canon SELPHY CP1500",
        "connected": true,
        "ready": true,
        "has_error": false,
        "status": "Idle",
        "error_state": "NoError",
        "message": "Máy in sẵn sàng."
    }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        device_id = (request.data.get('device_id') or '').strip()
        if not device_id:
            return Response(
                {'detail': 'Thiếu device_id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dev = PhotoboothDevice.objects.get(device_id=device_id, is_active=True)
        except PhotoboothDevice.DoesNotExist:
            return Response(
                {'detail': 'Thiết bị không tồn tại hoặc đã bị vô hiệu hóa.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        now = timezone.now()
        dev.printer_name = (request.data.get('printer_name') or '')[:200]
        dev.printer_connected = bool(request.data.get('connected', False))
        dev.printer_ready = bool(request.data.get('ready', False))
        dev.printer_has_error = bool(request.data.get('has_error', False))
        dev.printer_status = (request.data.get('status') or '')[:50]
        dev.printer_error_state = (request.data.get('error_state') or '')[:50]
        dev.printer_message = (request.data.get('message') or '')[:500]
        dev.current_screen = (request.data.get('current_screen') or '')[:50]
        dev.printer_status_at = now
        dev.last_seen_at = now
        dev.save(update_fields=[
            'printer_name', 'printer_connected', 'printer_ready',
            'printer_has_error', 'printer_status', 'printer_error_state',
            'printer_message', 'current_screen', 'printer_status_at', 'last_seen_at', 'updated_at',
        ])

        return Response({'ok': True})


class PrinterStatusListView(APIView):
    """
    GET /api/photobooth/devices/printer-status/
    CMS đọc trạng thái máy in của tất cả thiết bị active.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        devices = PhotoboothDevice.objects.filter(is_active=True).order_by('-printer_status_at')
        data = []
        for dev in devices:
            data.append({
                'id': dev.id,
                'device_id': dev.device_id,
                'name': dev.name,
                'printer_name': dev.printer_name,
                'connected': dev.printer_connected,
                'ready': dev.printer_ready,
                'has_error': dev.printer_has_error,
                'status': dev.printer_status,
                'error_state': dev.printer_error_state,
                'message': dev.printer_message,
                'printer_status_at': dev.printer_status_at.isoformat() if dev.printer_status_at else None,
                'last_seen_at': dev.last_seen_at.isoformat() if dev.last_seen_at else None,
                'current_screen': dev.current_screen,
            })
        return Response(data)
