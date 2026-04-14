from __future__ import annotations

import base64
import io
import logging

from PIL import Image
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PhotoboothDevice

logger = logging.getLogger(__name__)


class RemoveBackgroundSerializer(serializers.Serializer):
    """Payload for remove-background: same device_id as capture-options / register."""

    device_id = serializers.CharField(
        max_length=128,
        trim_whitespace=True,
        help_text='Photobooth device UUID from client (must be registered).',
    )
    image_base64 = serializers.CharField(
        help_text='Original frame as base64 (data URI or raw JPEG/PNG base64).',
    )
    background_code = serializers.CharField(
        max_length=64,
        trim_whitespace=True,
        help_text='Background code from Customize screen (must be assigned to device).',
    )


class RemoveBackgroundView(APIView):
    """
    POST /api/photobooth/remove-background/

    1. Nhận ảnh chụp (base64) + mã background.
    2. Dùng rembg (AI U²-Net) xóa phông nền người chụp.
    3. Ghép ảnh nền đã chọn phía sau.
    4. Trả ảnh kết quả dạng base64 JPEG.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        ser = RemoveBackgroundSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        device_id = ser.validated_data['device_id'].strip()
        raw_b64 = ser.validated_data['image_base64']
        bg_code = ser.validated_data['background_code'].strip()

        device = PhotoboothDevice.objects.filter(device_id=device_id).first()
        if not device:
            return Response(
                {'detail': 'Device is not registered.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # --- Decode ảnh gốc ---------------------------------------------------
        try:
            image_data = self._decode_base64_image(raw_b64)
            subject_img = Image.open(io.BytesIO(image_data)).convert('RGBA')
        except Exception:
            return Response(
                {'detail': 'Invalid base64 image data.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Background must be linked to this device (same as capture-options) ---
        bg_obj = device.backgrounds.filter(
            code__iexact=bg_code,
            is_active=True,
        ).first()
        if not bg_obj or not bg_obj.image:
            return Response(
                {
                    'detail': (
                        f'Background "{bg_code}" is not available for this device '
                        'or has no image file.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Xóa phông nền bằng rembg (AI) ------------------------------------
        try:
            from rembg import remove as rembg_remove

            input_bytes = self._pil_to_bytes(subject_img, fmt='PNG')
            output_bytes = rembg_remove(input_bytes)
            fg_img = Image.open(io.BytesIO(output_bytes)).convert('RGBA')
        except ImportError:
            logger.error('rembg is not installed; run poetry install / pip install rembg[cpu]')
            return Response(
                {'detail': 'Server missing rembg (AI background removal).'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception('rembg processing failed')
            return Response(
                {'detail': f'Background removal failed: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- Ghép nền mới -----------------------------------------------------
        try:
            bg_file = bg_obj.image.open('rb')
            bg_img = Image.open(bg_file).convert('RGBA')

            # Cover-fit: scale background to cover foreground size, then center-crop
            fg_w, fg_h = fg_img.size
            bg_w, bg_h = bg_img.size
            scale = max(fg_w / bg_w, fg_h / bg_h)
            new_w = round(bg_w * scale)
            new_h = round(bg_h * scale)
            bg_img = bg_img.resize((new_w, new_h), Image.LANCZOS)
            # Center crop to exact foreground dimensions
            left = (new_w - fg_w) // 2
            top = (new_h - fg_h) // 2
            bg_img = bg_img.crop((left, top, left + fg_w, top + fg_h))

            # Composite: background + foreground (người đã xóa phông)
            composite = Image.alpha_composite(bg_img, fg_img)
            composite = composite.convert('RGB')
        except Exception as exc:
            logger.exception('compositing failed')
            return Response(
                {'detail': f'Compositing failed: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- Trả kết quả dạng base64 JPEG -------------------------------------
        buf = io.BytesIO()
        composite.save(buf, format='JPEG', quality=92)
        result_b64 = base64.b64encode(buf.getvalue()).decode('ascii')

        return Response(
            {
                'result_image': f'data:image/jpeg;base64,{result_b64}',
            },
            status=status.HTTP_200_OK,
        )

    # ---------- Helpers --------------------------------------------------------

    @staticmethod
    def _decode_base64_image(raw: str) -> bytes:
        """Chấp nhận cả data URI (data:image/...;base64,...) lẫn raw base64."""
        if ',' in raw and raw.startswith('data:'):
            raw = raw.split(',', 1)[1]
        return base64.b64decode(raw)

    @staticmethod
    def _pil_to_bytes(img: Image.Image, fmt: str = 'PNG') -> bytes:
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        return buf.getvalue()
