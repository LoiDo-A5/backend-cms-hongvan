from __future__ import annotations

import base64
import io
import logging

import numpy as np
import requests as http_requests
from PIL import Image, ImageFilter
from django.conf import settings
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

        # --- Xóa phông nền (ưu tiên: Photoroom → remove.bg → rembg local) ------
        fg_img = None
        engine_used = None
        input_bytes = self._pil_to_bytes(subject_img, fmt='PNG')

        # 1) Photoroom API (trả phí, $0.02/ảnh Basic, chất lượng cao)
        photoroom_key = getattr(settings, 'PHOTOROOM_API_KEY', '')
        if photoroom_key and fg_img is None:
            fg_img, engine_used = self._remove_bg_photoroom(
                input_bytes, photoroom_key,
            )

        # 2) remove.bg API (trả phí, chuyên portrait, chất lượng cao nhất)
        removebg_key = getattr(settings, 'REMOVEBG_API_KEY', '')
        if removebg_key and fg_img is None:
            fg_img, engine_used = self._remove_bg_api(input_bytes, removebg_key)

        # 3) Fallback: rembg local (miễn phí)
        if fg_img is None:
            fg_img, engine_used, error_resp = self._remove_bg_rembg(subject_img)
            if error_resp is not None:
                return error_resp

        # --- Ghép nền mới -----------------------------------------------------
        try:
            bg_file = bg_obj.image.open('rb')
            bg_img = Image.open(bg_file).convert('RGBA')

            # Canvas = background full image (1000px wide, maintain background AR)
            # → background không bị crop/zoom, show toàn bộ hình background
            CANVAS_W = 1000
            bg_orig_w, bg_orig_h = bg_img.size
            canvas_h = round(bg_orig_h * CANVAS_W / bg_orig_w)
            bg_img = bg_img.resize((CANVAS_W, canvas_h), Image.LANCZOS)

            # Contain-fit foreground (người) trong canvas: giữ tỷ lệ người,
            # scale để vừa khít canvas (không overflow), căn giữa ngang + đáy dưới
            fg_w, fg_h = fg_img.size
            fg_scale = min(CANVAS_W / fg_w, canvas_h / fg_h)
            new_fg_w = round(fg_w * fg_scale)
            new_fg_h = round(fg_h * fg_scale)
            if new_fg_w != fg_w or new_fg_h != fg_h:
                fg_img = fg_img.resize((new_fg_w, new_fg_h), Image.LANCZOS)

            x_off = (CANVAS_W - new_fg_w) // 2
            # Bottom-align: người đứng sát đáy canvas, không bị cắt thân dưới
            y_off = canvas_h - new_fg_h

            # Composite: background + foreground (người đã xóa phông)
            canvas_img = bg_img.copy()
            canvas_img.alpha_composite(fg_img, dest=(x_off, y_off))
            composite = canvas_img.convert('RGB')
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
                'engine': engine_used,
            },
            status=status.HTTP_200_OK,
        )

    # ---------- Helpers --------------------------------------------------------

    @staticmethod
    def _remove_bg_api(image_bytes: bytes, api_key: str):
        """
        remove.bg API — trả phí, chất lượng cao nhất.
        Returns (fg_img, 'remove.bg') hoặc (None, None) nếu fail.
        """
        try:
            resp = http_requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': ('photo.png', image_bytes, 'image/png')},
                data={'size': 'auto', 'type': 'person'},
                headers={'X-Api-Key': api_key},
                timeout=30,
            )
            if resp.status_code == 200:
                fg_img = Image.open(io.BytesIO(resp.content)).convert('RGBA')
                logger.info('[REMOVE-BG] remove.bg API success')
                return fg_img, 'remove.bg'
            else:
                logger.warning(
                    '[REMOVE-BG] remove.bg API failed: %s - %s',
                    resp.status_code,
                    resp.text[:200],
                )
                return None, None
        except Exception as exc:
            logger.warning('[REMOVE-BG] remove.bg API error: %s', exc)
            return None, None

    @staticmethod
    def _remove_bg_photoroom(image_bytes: bytes, api_key: str):
        """
        Photoroom Remove Background API — $0.02/ảnh (Basic plan).
        Endpoint: POST https://sdk.photoroom.com/v1/segment
        Returns (fg_img, 'photoroom') hoặc (None, None) nếu fail.
        """
        try:
            resp = http_requests.post(
                'https://sdk.photoroom.com/v1/segment',
                files={'image_file': ('photo.png', image_bytes, 'image/png')},
                headers={'x-api-key': api_key},
                timeout=30,
            )
            if resp.status_code == 200:
                fg_img = Image.open(io.BytesIO(resp.content)).convert('RGBA')
                logger.info('[REMOVE-BG] Photoroom API success')
                return fg_img, 'photoroom'
            else:
                logger.warning(
                    '[REMOVE-BG] Photoroom API failed: %s - %s',
                    resp.status_code,
                    resp.text[:200],
                )
                return None, None
        except Exception as exc:
            logger.warning('[REMOVE-BG] Photoroom API error: %s', exc)
            return None, None

    def _remove_bg_rembg(self, subject_img: Image.Image):
        """
        rembg local — miễn phí, fallback.
        Returns (fg_img, 'rembg', None) hoặc (None, None, Response) nếu lỗi.
        """
        try:
            from rembg import remove as rembg_remove, new_session

            session = new_session('isnet-general-use')
            input_bytes = self._pil_to_bytes(subject_img, fmt='PNG')
            output_bytes = rembg_remove(
                input_bytes,
                session=session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=220,
                alpha_matting_background_threshold=20,
                alpha_matting_erode_size=4,
            )
            fg_img = Image.open(io.BytesIO(output_bytes)).convert('RGBA')
            fg_img = self._clean_alpha(fg_img)
            logger.info('[REMOVE-BG] rembg (isnet-general-use) success')
            return fg_img, 'rembg', None
        except ImportError:
            logger.error('rembg is not installed; run pip install rembg[cpu]')
            return None, None, Response(
                {'detail': 'Server missing rembg (AI background removal).'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception('rembg processing failed')
            return None, None, Response(
                {'detail': f'Background removal failed: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @staticmethod
    def _clean_alpha(img: Image.Image) -> Image.Image:
        """
        Dọn sạch alpha channel sau rembg:
        1. Loại bỏ ghost pixel (alpha < 30) → 100% trong suốt
        2. Pixel gần đặc (alpha > 225) → 100% đặc
        3. Smooth viền chuyển tiếp nhẹ để tránh răng cưa
        → Đảm bảo nền bị xóa sạch, người giữ nguyên chi tiết.
        """
        arr = np.array(img)
        alpha = arr[:, :, 3].copy()

        # Bước 1: xóa sạch ghost pixel — nền dính mờ
        alpha[alpha < 30] = 0

        # Bước 2: pixel gần đặc → đặc hoàn toàn — bảo vệ người
        alpha[alpha > 225] = 255

        arr[:, :, 3] = alpha
        cleaned = Image.fromarray(arr, 'RGBA')

        # Bước 3: smooth viền nhẹ (1px) để giảm răng cưa, không ảnh hưởng chi tiết
        smooth_alpha = cleaned.split()[3].filter(ImageFilter.SMOOTH)
        # Chỉ apply smooth cho vùng viền (alpha 30-225), giữ nguyên đặc/trong suốt
        orig_alpha = cleaned.split()[3]
        mask_arr = np.array(orig_alpha)
        smooth_arr = np.array(smooth_alpha)
        # Chỉ thay đổi pixel ở vùng viền chuyển tiếp
        edge_mask = (mask_arr > 0) & (mask_arr < 255)
        final_alpha = mask_arr.copy()
        final_alpha[edge_mask] = smooth_arr[edge_mask]
        cleaned.putalpha(Image.fromarray(final_alpha))

        return cleaned

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
