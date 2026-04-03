from __future__ import annotations

import base64
import io
import logging

from PIL import Image
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PhotoboothBackground

logger = logging.getLogger(__name__)


class RemoveBackgroundSerializer(serializers.Serializer):
    """Nhận ảnh chụp (base64 JPEG) + mã background để xóa phông và ghép nền mới."""

    image_base64 = serializers.CharField(
        help_text='Ảnh gốc dạng base64 (data URI hoặc raw base64 JPEG/PNG).',
    )
    background_code = serializers.CharField(
        max_length=64,
        help_text='Mã background đã chọn ở màn Tùy chỉnh.',
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

        raw_b64 = ser.validated_data['image_base64']
        bg_code = ser.validated_data['background_code']

        # --- Decode ảnh gốc ---------------------------------------------------
        try:
            image_data = self._decode_base64_image(raw_b64)
            subject_img = Image.open(io.BytesIO(image_data)).convert('RGBA')
        except Exception:
            return Response(
                {'detail': 'Không thể giải mã ảnh base64.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Lấy background ---------------------------------------------------
        bg_obj = PhotoboothBackground.objects.filter(
            code=bg_code, is_active=True,
        ).first()
        if not bg_obj or not bg_obj.image:
            return Response(
                {'detail': f'Background "{bg_code}" không tồn tại hoặc chưa có ảnh.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Xóa phông nền bằng rembg (AI) ------------------------------------
        try:
            from rembg import remove as rembg_remove

            input_bytes = self._pil_to_bytes(subject_img, fmt='PNG')
            output_bytes = rembg_remove(input_bytes)
            fg_img = Image.open(io.BytesIO(output_bytes)).convert('RGBA')
        except ImportError:
            logger.error('rembg chưa được cài đặt. Chạy: pip install rembg[gpu]')
            return Response(
                {'detail': 'Server chưa cài thư viện AI xóa phông (rembg).'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception('Lỗi khi xóa phông nền bằng rembg')
            return Response(
                {'detail': f'Lỗi xử lý AI xóa phông: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- Ghép nền mới -----------------------------------------------------
        try:
            bg_file = bg_obj.image.open('rb')
            bg_img = Image.open(bg_file).convert('RGBA')

            # Scale background để khớp kích thước ảnh chụp
            bg_img = bg_img.resize(fg_img.size, Image.LANCZOS)

            # Composite: background + foreground (người đã xóa phông)
            composite = Image.alpha_composite(bg_img, fg_img)
            composite = composite.convert('RGB')
        except Exception as exc:
            logger.exception('Lỗi khi ghép ảnh nền')
            return Response(
                {'detail': f'Lỗi ghép ảnh nền: {exc}'},
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
