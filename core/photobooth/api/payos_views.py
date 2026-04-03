from __future__ import annotations

import json
import logging
import secrets
import uuid
import urllib.error
import urllib.request
from datetime import timedelta
from datetime import timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from django.http import HttpResponse
from django.utils.html import escape
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import CapturePackage, PaymentOrder
from core.photobooth.payos import (
    build_create_payment_signature,
    normalize_payos_description,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)

_VN_TZ = ZoneInfo('Asia/Ho_Chi_Minh')

PAYOS_API_BASE = 'https://api-merchant.payos.vn'
# payOS orderCode kiểu Int32; cần duy nhất trên kênh — không dùng trực tiếp id DB (dễ trùng lịch sử → 403/1010).
_PAYOS_ORDER_CODE_MAX = 2_147_483_647


def _allocate_payos_order_code() -> int:
    """Mã Int32 phân bố rộng (UUID) — tránh trùng mã đã dùng trên payOS hoặc trùng vùng nhỏ."""
    for _ in range(64):
        n = (uuid.uuid4().int % (_PAYOS_ORDER_CODE_MAX - 1)) + 1
        if not PaymentOrder.objects.filter(payos_order_code=n).exists():
            return n
    raise RuntimeError('Không sinh được mã orderCode payOS duy nhất')


def _payos_error_hint(raw: dict) -> str:
    desc = str(raw.get('desc') or '')
    code = str(raw.get('code') or '')
    if '1010' in desc:
        # payOS không công bố chi tiết 403/1010; thực tế hay gặp khi tài khoản/kênh không đủ điều kiện tạo link.
        return (
            'Lỗi payOS 1010 (Forbidden): cổng từ chối tạo link — thường không phải do code tích hợp. '
            'Kiểm tra trên my.payos.vn theo thứ tự: (1) Tổ chức đã xác thực. '
            '(2) Đã liên kết ít nhất một tài khoản ngân hàng với payOS. '
            '(3) Kênh thanh toán đã tạo xong; Client ID / API Key / Checksum copy đúng cùng một kênh. '
            '(4) Còn gói giao dịch (hết gói thì bị hạn chế tạo đơn). '
            '(5) Nếu vẫn lỗi: gửi support@payos.vn kèm mã lỗi 1010 và Client ID (không gửi API Key).'
        )
    if code == '403':
        return (
            'HTTP 403 từ payOS: không có quyền tạo link — thường do kênh/khóa API hoặc tài khoản chưa đủ điều kiện '
            '(xác thực tổ chức, liên kết NH, gói giao dịch). Xem hint cho mã 1010 nếu desc có chứa 1010.'
        )
    return (
        'Thường gặp: sai Checksum Key / Client ID / API Key so với kênh trên my.payos.vn; '
        'chữ ký không khớp; returnUrl/cancelUrl không hợp lệ (thử HTTPS + ngrok).'
    )


def _payos_api_success(raw: dict) -> bool:
    """payOS trả code === '00' (string) khi thành công; có thể gặp biến thể kiểu."""
    if not isinstance(raw, dict):
        return False
    c = raw.get('code')
    if c is None:
        return False
    s = str(c).strip()
    if s == '00' or s == '0':
        return True
    return False


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


def _post_payos_payment_request(payload: dict) -> dict:
    client_id = (settings.PAYOS_CLIENT_ID or '').strip()
    api_key = (settings.PAYOS_API_KEY or '').strip()
    url = f'{PAYOS_API_BASE}/v2/payment-requests'
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'x-client-id': client_id,
        'x-api-key': api_key,
    }
    partner = (getattr(settings, 'PAYOS_PARTNER_CODE', '') or '').strip()
    if partner:
        headers['x-partner-code'] = partner
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')
        logger.warning('payOS create HTTP %s: %s', e.code, err_body[:500])
        try:
            return json.loads(err_body)
        except json.JSONDecodeError:
            return {'code': str(e.code), 'desc': err_body[:200]}
    except urllib.error.URLError as e:
        logger.exception('payOS create network error')
        raise RuntimeError(f'Không kết nối được payOS: {e}') from e


class PayosCreatePaymentView(APIView):
    """
    POST /api/payments/payos/create/

    Body: { "package_id": 1 } hoặc { "package_code": "economy" }, optional "booth_id"
    Trả checkout_url + qr_code (VietQR). order_id = txn_ref (id DB dạng chuỗi) để poll;
    payOS nhận orderCode riêng (payos_order_code) để tránh trùng mã trên cổng.
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

        checksum = (settings.PAYOS_CHECKSUM_KEY or '').strip()
        return_url = (settings.PAYOS_RETURN_URL or '').strip()
        cancel_url = (settings.PAYOS_CANCEL_URL or '').strip()
        desc = normalize_payos_description(f'{pkg.code} {pkg.name}')

        expired_at_ts = int(expires_at_utc.timestamp())
        signature = build_create_payment_signature(
            amount=order.amount_vnd,
            cancel_url=cancel_url,
            description=desc,
            order_code=order.payos_order_code,
            return_url=return_url,
            checksum_key=checksum,
        )

        payload = {
            'orderCode': int(order.payos_order_code),
            'amount': int(order.amount_vnd),
            'description': desc,
            'cancelUrl': cancel_url,
            'returnUrl': return_url,
            'signature': signature,
        }
        if getattr(settings, 'PAYOS_SEND_EXPIRED_AT', False):
            payload['expiredAt'] = expired_at_ts

        logger.info(
            'payOS create: orderCode=%s amount=%s desc=%r send_expired=%s',
            order.payos_order_code,
            order.amount_vnd,
            desc,
            getattr(settings, 'PAYOS_SEND_EXPIRED_AT', False),
        )

        try:
            raw = _post_payos_payment_request(payload)
        except RuntimeError as e:
            order.delete()
            logger.error('payOS create: network error %s', e)
            return Response(
                {
                    'detail': str(e),
                    'hint': 'Kiểm tra container có ra internet (DNS/firewall) tới api-merchant.payos.vn.',
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if not _payos_api_success(raw):
            order.delete()
            msg = raw.get('desc') or raw.get('message') or 'payOS từ chối tạo link.'
            logger.error(
                'payOS create rejected: code=%s desc=%s raw=%s',
                raw.get('code'),
                raw.get('desc'),
                raw,
            )
            return Response(
                {
                    'detail': msg,
                    'payos_code': raw.get('code'),
                    'payos_desc': raw.get('desc'),
                    'payos': raw,
                    'hint': _payos_error_hint(raw),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        data = raw.get('data') or {}
        checkout_url = (data.get('checkoutUrl') or '').strip()
        qr_code = (data.get('qrCode') or '').strip()
        link_id = (data.get('paymentLinkId') or '')[:64]

        if link_id:
            order.payos_payment_link_id = link_id
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
            body = request.data if isinstance(request.data, dict) else {}
        except Exception:
            body = {}

        sig = (body.get('signature') or '').strip()
        data = body.get('data')
        if not isinstance(data, dict):
            return Response({'detail': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)

        checksum = (settings.PAYOS_CHECKSUM_KEY or '').strip()
        if not verify_webhook_signature(data, sig, checksum):
            logger.warning('payOS webhook invalid signature')
            return Response({'detail': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)

        if body.get('code') != '00':
            return Response({'detail': 'ignored'}, status=status.HTTP_200_OK)
        if body.get('success') is False:
            return Response({'detail': 'ignored'}, status=status.HTTP_200_OK)

        try:
            order_code = int(data.get('orderCode'))
        except (TypeError, ValueError):
            return Response({'detail': 'Bad orderCode'}, status=status.HTTP_400_BAD_REQUEST)

        amount = data.get('amount')
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return Response({'detail': 'Bad amount'}, status=status.HTTP_400_BAD_REQUEST)

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

        inner_code = (data.get('code') or '')[:8]
        ref = (data.get('reference') or data.get('paymentLinkId') or '')[:64]
        order.vnp_response_code = inner_code or '00'
        order.vnp_transaction_no = ref
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
