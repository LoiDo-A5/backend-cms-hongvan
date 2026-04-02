"""
Webhook VietQR.IO / Casso — nhận thông báo chuyển khoản khớp đơn photobooth.

Tài liệu: https://www.vietqr.io/paymentRequests/#operation/webhook-merchant

Đăng ký URL công khai (HTTPS) trên VietQR, ví dụ::
    POST https://your-domain.com/api/payments/vietqr/webhook/

Khớp đơn: ``PaymentOrder.txn_ref`` (trùng ``order.orderId`` / ``addInfo`` trên QR) phải xuất hiện
trong nội dung giao dịch — tìm trong ``description``, ``reference``, ``tid``, v.v. Casso có thể
tách ``reference`` và ``description``; VietQR thường gửi ``description`` = nội dung CK.

**Casso Webhook V2** gửi ``data`` là **một object** (không phải mảng); code chuẩn hóa thành một
bản ghi để xử lý giống VietQR.

Cấu hình: ``VIETQR_WEBHOOK_SECRET`` — nếu đặt, request phải gửi kèm
``Authorization: Bearer <secret>``, ``X-VietQR-Token``, hoặc ``secure-token`` (Casso V1).
"""

from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PaymentOrder

logger = logging.getLogger(__name__)


def _webhook_secret_ok(request) -> bool:
    expected = getattr(settings, 'VIETQR_WEBHOOK_SECRET', '') or ''
    if not expected:
        return True
    auth = (request.headers.get('Authorization') or '').strip()
    if auth == f'Bearer {expected}':
        return True
    if auth == expected:
        return True
    token = (request.headers.get('X-VietQR-Token') or '').strip()
    if token == expected:
        return True
    for hdr in ('X-Secure-Token', 'Secure-Token', 'secure-token'):
        secure = (request.headers.get(hdr) or '').strip()
        if secure == expected:
            return True
    return False


def _to_int_amount(raw) -> Optional[int]:
    if raw is None:
        return None
    try:
        return int(round(float(raw)))
    except (TypeError, ValueError):
        return None


def _transaction_items_from_body(body: dict) -> list[dict]:
    """
    VietQR: ``data`` là list[object].
    Casso Webhook V2: ``data`` là một object giao dịch (không phải list).
    """
    raw = body.get('data')
    if raw is None:
        return []
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


def _root_indicates_skip(body: dict) -> bool:
    """Casso: ``error`` != 0. VietQR: ``code`` ở root khác ``00`` (bỏ qua toàn bộ)."""
    if 'error' in body:
        try:
            if int(body['error']) != 0:
                return True
        except (TypeError, ValueError):
            return True
    c = body.get('code')
    if c is None:
        return False
    return str(c).strip() != '00'


def _match_text_for_item(item: dict) -> str:
    """Ghép các trường thường có mã đơn / nội dung CK (Casso tách reference vs description)."""
    parts: list[str] = []
    for key in (
        'description',
        'reference',
        'addInfo',
        'content',
        'message',
        'remarks',
        'tid',
    ):
        v = item.get(key)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            parts.append(s)
    return ' '.join(parts)


def _find_order_for_vietqr_item(item: dict) -> Optional[PaymentOrder]:
    """Tìm đơn PENDING — ưu tiên ``orderCode`` (Payment KIT = ``PaymentOrder.pk``), sau đó amount + mô tả."""
    amount = _to_int_amount(item.get('amount'))
    desc = _match_text_for_item(item)

    qs = PaymentOrder.objects.filter(status=PaymentOrder.Status.PENDING)
    now = timezone.now()

    # VietQR Payment KIT: webhook gửi orderCode trùng orderCode lúc tạo paymentRequests.
    oc = item.get('orderCode')
    if oc is not None:
        try:
            pk = int(oc)
        except (TypeError, ValueError):
            pk = None
        if pk is not None:
            o = qs.filter(pk=pk).first()
            if o and now <= o.expires_at:
                if amount is not None and amount != o.amount_vnd:
                    logger.warning(
                        'VietQR webhook: amount mismatch for pk=%s expected=%s got=%s',
                        pk,
                        o.amount_vnd,
                        amount,
                    )
                    return None
                return o

    # Khớp trực tiếp mã đơn = toàn bộ một trường (ít gặp nhưng rõ ràng)
    direct = qs.filter(txn_ref=desc).first()
    if direct and now <= direct.expires_at:
        if amount is not None and amount != direct.amount_vnd:
            logger.warning(
                'VietQR webhook: amount mismatch for txn_ref=%s expected=%s got=%s',
                direct.txn_ref,
                direct.amount_vnd,
                amount,
            )
            return None
        return direct

    candidates = [o for o in qs if now <= o.expires_at]
    matched = []
    for o in candidates:
        if amount is not None and o.amount_vnd != amount:
            continue
        if o.txn_ref in desc:
            matched.append(o)

    if len(matched) == 1:
        return matched[0]
    if len(matched) > 1:
        logger.warning(
            'VietQR webhook: ambiguous match for text=%r count=%s',
            desc[:200],
            len(matched),
        )
    return None


def _item_marks_success(item: dict) -> bool:
    """Theo mẫu VietQR: từng phần tử data có thể có code/desc."""
    c = item.get('code')
    if c is None:
        return True
    return str(c) == '00'


class VietqrWebhookView(APIView):
    """
    POST /api/payments/vietqr/webhook/

    Body JSON — VietQR (ví dụ)::

        {
          "code": "00",
          "data": [{"amount": 79000, "description": "PB-20260402-...", ...}]
        }

    Casso Webhook V2 (``data`` là object)::

        {"error": 0, "data": {"amount": 79000, "description": "...", "reference": "...", ...}}
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not _webhook_secret_ok(request):
            logger.warning('VietQR webhook: unauthorized')
            return Response(
                {'detail': 'Unauthorized'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        body = request.data
        if not isinstance(body, dict):
            return Response({'detail': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        if _root_indicates_skip(body):
            logger.info(
                'VietQR webhook: skip body (error=%s code=%s)',
                body.get('error'),
                body.get('code'),
            )
            return Response(
                {'received': True, 'processed': 0, 'skipped': True, 'success': True},
                status=status.HTTP_200_OK,
            )

        data_list = _transaction_items_from_body(body)

        processed = 0
        for item in data_list:
            if not isinstance(item, dict):
                continue
            if not _item_marks_success(item):
                logger.info('VietQR webhook: skip item with code=%s', item.get('code'))
                continue

            order = _find_order_for_vietqr_item(item)
            if not order:
                logger.info(
                    'VietQR webhook: no matching order amount=%s text=%r',
                    item.get('amount'),
                    _match_text_for_item(item)[:200],
                )
                continue

            if order.status == PaymentOrder.Status.PAID:
                processed += 1
                continue

            ref = (
                item.get('tid')
                or item.get('reference')
                or item.get('transactionDatetime')
                or item.get('transactionDateTime')
            )
            ref_s = str(ref)[:32] if ref is not None else ''

            order.status = PaymentOrder.Status.PAID
            order.paid_at = timezone.now()
            if ref_s:
                order.vnp_transaction_no = ref_s
            order.save(
                update_fields=['status', 'paid_at', 'vnp_transaction_no', 'updated_at']
            )
            processed += 1
            logger.info('VietQR webhook: marked paid txn_ref=%s', order.txn_ref)

        # Trả 200; ``success`` phục vụ Casso Strict mode (yêu cầu JSON success khi HTTP 200).
        return Response(
            {'received': True, 'processed': processed, 'success': True},
            status=status.HTTP_200_OK,
        )
