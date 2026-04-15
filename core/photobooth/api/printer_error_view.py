from __future__ import annotations

import logging
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

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
        valid_types = ['paper_jam', 'no_paper', 'disconnected', 'hardware_error', 'print_failed']
        if error_type not in valid_types:
            error_type = 'print_failed'

        # Get device location if available
        location = None
        try:
            from core.photobooth.models import PhotoboothDevice
            device = PhotoboothDevice.objects.filter(device_id=device_id).first()
            if device and device.location:
                location = device.location.name if hasattr(device.location, 'name') else str(device.location)
        except Exception as e:
            logger.warning(f"[PRINTER-ERROR] Could not get device location: {e}")

        # Queue Discord notification
        queued = False
        if getattr(settings, 'DISCORD_WEBHOOK_URL', ''):
            try:
                from common.tasks.discord import send_discord_printer_alert
                send_discord_printer_alert.delay(
                    device_id=device_id,
                    error_type=error_type,
                    printer_name=printer_name,
                    message=message or f"Lỗi máy in: {error_type}",
                    location=location,
                )
                queued = True
                logger.info(f"[PRINTER-ERROR] Queued Discord alert for {device_id}: {error_type}")
            except Exception as e:
                logger.error(f"[PRINTER-ERROR] Failed to queue Discord alert: {e}")

        return Response({'status': 'ok', 'queued': queued})
