from __future__ import annotations

import json
import logging
import secrets
import uuid
from datetime import timedelta
from datetime import timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from django.http import HttpResponse
from django.utils.html import escape
from django.utils import timezone
from payos import PayOS, APIError as PayOSAPIError
from payos.types import CreatePaymentLinkRequest
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import CapturePackage, PaymentOrder
from core.photobooth.models.photobooth_device import PhotoboothDevice

logger = logging.getLogger(__name__)

_VN_TZ = ZoneInfo('Asia/Ho_Chi_Minh')

_PAYOS_ORDER_CODE_MAX = 2_147_483_647

_payos_client = None


def _get_payos_client() -> PayOS:
    """Lazy-init payOS client singleton (tránh lỗi khi settings chưa sẵn sàng lúc import)."""
    global _payos_client
    if _payos_client is None:
        _payos_client = PayOS(
            client_id=(settings.PAYOS_CLIENT_ID or '').strip(),
            api_key=(settings.PAYOS_API_KEY or '').strip(),
            checksum_key=(settings.PAYOS_CHECKSUM_KEY or '').strip(),
        )
    return _payos_client


def _allocate_payos_order_code() -> int:
    for _ in range(64):
        n = (uuid.uuid4().int % (_PAYOS_ORDER_CODE_MAX - 1)) + 1
        if not PaymentOrder.objects.filter(payos_order_code=n).exists():
            return n
    raise RuntimeError('Không sinh được mã orderCode payOS duy nhất')


def _now_vietnam():
    return timezone.now().astimezone(_VN_TZ)


def _payos_configured() -> bool:
    return bool(
        (getattr(settings, 'PAYOS_CLIENT_ID', '') or '').strip()
        and (getattr(settings, 'PAYOS_API_KEY', '') or '').strip()
        and (getattr(settings, 'PAYOS_CHECKSUM_KEY', '') or '').strip()
        and (getattr(settings, 'PAYOS_RETURN_URL', '') or '').strip()
        and (getattr(settings, 'PAYOS_CANCEL_URL', '') or '').strip(),
    )


def _normalize_description(text: str) -> str:
    """payOS description tối đa 25 ký tự, chỉ ASCII + số."""
    import re
    cleaned = re.sub(r'[^A-Za-z0-9 ]', '', text)
    return cleaned[:25].strip() or 'Photobooth'


class PayosCreatePaymentView(APIView):
    """
    POST /api/payments/payos/create/

    Body: { "package_id": 1, "device_id": "...", "booth_id": "..." }
    Trả checkout_url + qr_code (VietQR). order_id = txn_ref để poll.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not _payos_configured():
            return Response(
                {
                    'detail': (
                        'payOS chưa cấu hình (PAYOS_CLIENT_ID, PAYOS_API_KEY, '
                        'PAYOS_CHECKSUM_KEY, PAYOS_RETURN_URL, PAYOS_CANCEL_URL).'
                    ),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        package_id = request.data.get('package_id')
        package_code = request.data.get('package_code')
        booth_id = (request.data.get('booth_id') or '')[:64]
        device_id = (request.data.get('device_id') or '').strip()

        device = None
        if device_id:
            device = PhotoboothDevice.objects.filter(device_id=device_id, is_active=True).first()

        pkg = None
        if package_id is not None:
            pkg = CapturePackage.objects.filter(id=package_id, is_active=True).first()
        elif package_code:
            pkg = CapturePackage.objects.filter(code=package_code, is_active=True).first()

        if not pkg:
            return Response(
                {'detail': 'Không tìm thấy gói hợp lệ.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now_vn = _now_vietnam()
        expires_vn = now_vn + timedelta(minutes=15)
        expires_at_utc = expires_vn.astimezone(dt_timezone.utc)
        tmp_txn = f'TMP-{secrets.token_hex(12)}'

        order = PaymentOrder.objects.create(
            txn_ref=tmp_txn,
            amount_vnd=pkg.amount_vnd,
            capture_package=pkg,
            device=device,
            booth_id=booth_id,
            expires_at=expires_at_utc,
            status=PaymentOrder.Status.PENDING,
        )
        order.txn_ref = str(order.pk)
        try:
            poc = _allocate_payos_order_code()
        except RuntimeError as e:
            order.delete()
            logger.error('payOS: %s', e)
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        order.payos_order_code = poc
        order.save(update_fields=['txn_ref', 'payos_order_code', 'updated_at'])

        return_url = (settings.PAYOS_RETURN_URL or '').strip()
        cancel_url = (settings.PAYOS_CANCEL_URL or '').strip()
        desc = _normalize_description(f'{pkg.code} {pkg.name}')

        payment_data = CreatePaymentLinkRequest(
            order_code=int(order.payos_order_code),
            amount=int(order.amount_vnd),
            description=desc,
            cancel_url=cancel_url,
            return_url=return_url,
        )

        logger.info(
            'payOS create: orderCode=%s amount=%s desc=%r',
            order.payos_order_code,
            order.amount_vnd,
            desc,
        )

        try:
            client = _get_payos_client()
            response = client.payment_requests.create(payment_data=payment_data)
        except PayOSAPIError as e:
            order.delete()
            logger.error(
                'payOS create rejected: code=%s desc=%s',
                e.error_code,
                e.error_desc,
            )
            return Response(
                {
                    'detail': e.error_desc or 'payOS từ chối tạo link.',
                    'payos_code': e.error_code,
                    'payos_desc': e.error_desc,
                    'hint': (
                        'Kiểm tra trên my.payos.vn: (1) Tổ chức đã xác thực. '
                        '(2) Đã liên kết tài khoản ngân hàng. '
                        '(3) Client ID / API Key / Checksum copy đúng cùng một kênh. '
                        '(4) Còn gói giao dịch.'
                    ),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            order.delete()
            logger.exception('payOS create: unexpected error')
            return Response(
                {
                    'detail': str(e),
                    'hint': 'Kiểm tra container có ra internet (DNS/firewall) tới api-merchant.payos.vn.',
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        checkout_url = getattr(response, 'checkout_url', '') or ''
        qr_code = getattr(response, 'qr_code', '') or ''
        link_id = getattr(response, 'payment_link_id', '') or ''

        if link_id:
            order.payos_payment_link_id = str(link_id)[:64]
            order.save(update_fields=['payos_payment_link_id', 'updated_at'])

        return Response(
            {
                'checkout_url': checkout_url,
                'qr_code': qr_code,
                'order_id': order.txn_ref,
                'amount_vnd': order.amount_vnd,
                'expired_at': int(expires_at_utc.timestamp() * 1000),
                'package': {
                    'id': pkg.id,
                    'code': pkg.code,
                    'name': pkg.name,
                    'print_count': pkg.print_count,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class PayosWebhookView(APIView):
    """
    POST /api/payments/payos/webhook/ — payOS gửi khi thanh toán (đăng ký URL trên my.payos.vn).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not _payos_configured():
            return Response({'detail': 'payOS not configured'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            raw_body = request.body
        except Exception:
            return Response({'detail': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify webhook signature using official SDK
        try:
            client = _get_payos_client()
            webhook_data = client.webhooks.verify(raw_body)
        except Exception as e:
            # PayOS confirmWebhook gửi ping kiểm tra — có thể không verify được.
            # Trả 200 để PayOS xác nhận URL hợp lệ, nhưng không xử lý dữ liệu.
            logger.info('payOS webhook verification failed (likely confirm ping): %s', e)
            return Response({'ok': True}, status=status.HTTP_200_OK)

        # payOS gửi confirmation ping khi đăng ký webhook (orderCode=0, amount=0).
        order_code = webhook_data.order_code
        amount = webhook_data.amount
        if order_code == 0:
            logger.info('payOS webhook confirmation ping received — OK')
            return Response({'ok': True}, status=status.HTTP_200_OK)

        order = (
            PaymentOrder.objects.filter(payos_order_code=order_code).first()
            or PaymentOrder.objects.filter(pk=order_code).first()
        )
        if not order:
            return Response({'detail': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if amount != order.amount_vnd:
            logger.warning(
                'payOS webhook amount mismatch order=%s expected=%s got=%s',
                order_code,
                order.amount_vnd,
                amount,
            )
            return Response({'detail': 'Amount mismatch'}, status=status.HTTP_400_BAD_REQUEST)

        if order.status == PaymentOrder.Status.PAID:
            return Response({'ok': True, 'detail': 'Already paid'}, status=status.HTTP_200_OK)

        if timezone.now() > order.expires_at and order.status == PaymentOrder.Status.PENDING:
            order.status = PaymentOrder.Status.EXPIRED
            order.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Expired'}, status=status.HTTP_200_OK)

        ref = str(webhook_data.reference or webhook_data.payment_link_id or '')[:64]
        order.vnp_transaction_no = ref
        order.vnp_response_code = '00'
        order.vnp_transaction_status = '00'
        order.status = PaymentOrder.Status.PAID
        order.paid_at = timezone.now()
        order.save()

        return Response({'ok': True}, status=status.HTTP_200_OK)


class PayosReturnView(APIView):
    """GET /api/payments/payos/return/ — redirect sau thanh toán (chỉ hiển thị)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        code = request.GET.get('code', '')
        order_id = request.GET.get('id', '')
        body = (
            '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Thanh toán payOS</title></head>'
            '<body><p>Đã quay lại từ payOS.</p>'
            f'<p>code: {escape(code)}</p>'
            f'<p>id: {escape(order_id)}</p>'
            '<p>Bạn có thể đóng trang và quay lại photobooth — ứng dụng sẽ tự xác nhận qua webhook / kiểm tra định kỳ.</p>'
            '</body></html>'
        )
        return HttpResponse(body, content_type='text/html; charset=utf-8')


class PayosCancelReturnView(APIView):
    """GET /api/payments/payos/cancel/ — sau khi hủy trên payOS."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        body = (
            '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Hủy thanh toán</title></head>'
            '<body><p>Giao dịch đã hủy hoặc chưa hoàn tất.</p>'
            '<p>Bạn có thể đóng trang và quay lại photobooth.</p></body></html>'
        )
        return HttpResponse(body, content_type='text/html; charset=utf-8')
