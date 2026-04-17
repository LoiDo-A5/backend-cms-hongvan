from __future__ import annotations

import logging
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils.matrix_notify import notify_printer_error

logger = logging.getLogger(__name__)


class PrinterErrorView(APIView):
    """
    POST /api/photobooth/printer-error/
    Electron app gửi thông báo khi máy in gặp lỗi.

    Body: {
        "device_id": "<uuid>",
        "error_type": "paper_jam|no_paper|disconnected|hardware_error|print_failed",
        "printer_name": "Canon SELPHY CP1500",
        "message": "Chi tiết lỗi...",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        device_id = (request.data.get('device_id') or '').strip()
        error_type = (request.data.get('error_type') or 'print_failed').strip()
        printer_name = (request.data.get('printer_name') or 'Unknown').strip()
        message = (request.data.get('message') or '').strip()

        if not device_id:
            return Response(
                {'detail': 'Thiếu device_id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate error_type
        valid_types = ['paper_jam', 'no_paper', 'low_paper', 'no_ink', 'low_ink',
                       'disconnected', 'offline', 'hardware_error', 'print_failed', 'cover_open']
        if error_type not in valid_types:
            error_type = 'print_failed'

        # Get device name
        device_name = device_id
        try:
            from core.photobooth.models import PhotoboothDevice
            device = PhotoboothDevice.objects.filter(device_id=device_id).first()
            if device:
                device_name = device.name or device_id
        except Exception as e:
            logger.warning(f"[PRINTER-ERROR] Could not get device: {e}")

        logger.info(f"[PRINTER-ERROR] {device_name}: {error_type} - {printer_name} - {message}")

        # Push Matrix notification
        notify_printer_error(
            device_name=device_name,
            error_key=error_type,
            detail=message,
            printer_name=printer_name,
        )

        return Response({'status': 'ok'})
