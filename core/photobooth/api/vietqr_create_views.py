"""
POST /api/payments/vietqr/create/ — tạo đơn + link thanh toán qua ``api.vietqr.io/v2/paymentRequests`` (PDF).
"""
from __future__ import annotations

import logging
from datetime import timedelta
from datetime import timezone as dt_timezone

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.api.vnpay_views import _make_txn_ref, _now_vietnam
from core.photobooth.models import CapturePackage, PaymentOrder
from core.photobooth.vietqr_api import VietQrApiError, post_payment_request

logger = logging.getLogger(__name__)


def _urls_ok() -> tuple[str, str] | None:
    cancel_url = (getattr(settings, 'VIETQR_CANCEL_URL', None) or '').strip()
    success_url = (getattr(settings, 'VIETQR_SUCCESS_URL', None) or '').strip()
    if not cancel_url:
        cancel_url = success_url
    if not success_url:
        success_url = cancel_url
    if not cancel_url or not success_url:
        return None
    return cancel_url, success_url


def _vietqr_payment_configured() -> bool:
    if not (
        (getattr(settings, 'VIETQR_CLIENT_ID', '') or '').strip()
        and (getattr(settings, 'VIETQR_API_KEY', '') or '').strip()
    ):
        return False
    return _urls_ok() is not None


class VietqrCreatePaymentView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not _vietqr_payment_configured():
            return Response(
                {
                    'detail': (
                        'Thiếu VIETQR_CLIENT_ID, VIETQR_API_KEY hoặc VIETQR_CANCEL_URL / VIETQR_SUCCESS_URL.'
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        urls = _urls_ok()
        assert urls is not None
        cancel_url, return_url = urls

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
        txn_ref = _make_txn_ref()

        order = PaymentOrder.objects.create(
            txn_ref=txn_ref,
            amount_vnd=pkg.amount_vnd,
            capture_package=pkg,
            booth_id=booth_id,
            expires_at=expires_at_utc,
            status=PaymentOrder.Status.PENDING,
        )

        template = (getattr(settings, 'VIETQR_PAYMENT_TEMPLATE', None) or 'compact').strip()
        description = order.txn_ref
        if len(description) > 200:
            description = description[:200]

        payload = {
            'orderCode': order.pk,
            'amount': order.amount_vnd,
            'description': description,
            'template': template,
            'items': [],
            'cancelUrl': cancel_url,
            'successUrl': return_url,
        }

        try:
            raw = post_payment_request(payload)
        except VietQrApiError as e:
            logger.warning('Tạo link thanh toán thất bại: %s', e)
            order.delete()
            detail = str(e)
            if e.body:
                detail = f'{detail} — {e.body[:400]}'
            return Response({'detail': detail}, status=status.HTTP_502_BAD_GATEWAY)

        code = raw.get('code')
        data = raw.get('data')
        if code != '00' or not isinstance(data, dict):
            logger.warning('Phản hồi không thành công: %s', raw)
            order.delete()
            return Response(
                {
                    'detail': raw.get('desc') or 'Từ chối tạo link thanh toán.',
                    'provider': raw,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        checkout = (data.get('checkoutUrl') or data.get('checkout_url') or '').strip()
        if not checkout:
            logger.warning('Thiếu checkoutUrl: %s', data)
            order.delete()
            return Response(
                {'detail': 'Không tìm thấy checkoutUrl trong phản hồi.', 'provider': raw},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                'payment_url': checkout,
                'order_id': txn_ref,
                'amount_vnd': order.amount_vnd,
                'expired_at': int(expires_at_utc.timestamp() * 1000),
                'package': {'id': pkg.id, 'code': pkg.code, 'name': pkg.name},
                'vietqr_order_code': order.pk,
            },
            status=status.HTTP_201_CREATED,
        )
