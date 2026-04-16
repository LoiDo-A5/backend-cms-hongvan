"""
PayPal REST API v2 — tạo đơn thanh toán, capture, kiểm tra trạng thái.
Sử dụng Client ID + Secret Key (server-to-server), **không cần SDK**.
Khách quốc tế quét QR → mở trang approve PayPal → thanh toán → PayPal redirect về return URL.
App Electron poll GET /api/payments/status/<order_id>/ → backend gọi PayPal API kiểm tra → nếu APPROVED thì auto capture → cập nhật PAID.
"""
from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from datetime import timezone as dt_timezone

import requests
from django.conf import settings
from django.utils import timezone
from django.utils.html import escape
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import CapturePackage, PaymentOrder
from core.photobooth.models.photobooth_device import PhotoboothDevice

logger = logging.getLogger(__name__)

# ── helpers ──────────────────────────────────────────────────────────────

_access_token_cache: dict = {}  # {'token': str, 'expires_at': float}


def _paypal_configured() -> bool:
    return bool(
        (getattr(settings, 'PAYPAL_CLIENT_ID', '') or '').strip()
        and (getattr(settings, 'PAYPAL_SECRET_KEY', '') or '').strip()
    )


def _paypal_base_url() -> str:
    mode = (getattr(settings, 'PAYPAL_MODE', '') or 'live').strip().lower()
    if mode == 'sandbox':
        return 'https://api-m.sandbox.paypal.com'
    return 'https://api-m.paypal.com'


def _get_access_token() -> str:
    """OAuth 2.0 client_credentials — cache token until expiry (minus 60s buffer)."""
    import time

    now = time.time()
    cached = _access_token_cache.get('token')
    if cached and _access_token_cache.get('expires_at', 0) > now:
        return cached

    client_id = (settings.PAYPAL_CLIENT_ID or '').strip()
    secret = (settings.PAYPAL_SECRET_KEY or '').strip()

    resp = requests.post(
        f'{_paypal_base_url()}/v1/oauth2/token',
        data={'grant_type': 'client_credentials'},
        auth=(client_id, secret),
        headers={'Accept': 'application/json'},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    token = data['access_token']
    expires_in = int(data.get('expires_in', 3600))
    _access_token_cache['token'] = token
    _access_token_cache['expires_at'] = now + expires_in - 60

    return token


def _paypal_headers() -> dict:
    token = _get_access_token()
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


def _vnd_to_usd(amount_vnd: int) -> str:
    """Quy đổi VND → USD (tỷ giá đơn giản). PayPal không hỗ trợ VND trực tiếp."""
    rate = 25_500  # ~25,500 VND/USD — đủ dùng cho photobooth
    usd = amount_vnd / rate
    return f'{usd:.2f}'


# ── Views ────────────────────────────────────────────────────────────────


class PaypalCreatePaymentView(APIView):
    """
    POST /api/payments/paypal/create/
    Body: { "package_id": 1, "booth_id": "...", "device_id": "..." }
    Trả approval_url để khách quét QR (PayPal checkout page).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not _paypal_configured():
            return Response(
                {'detail': 'PayPal chưa cấu hình (PAYPAL_CLIENT_ID, PAYPAL_SECRET_KEY).'},
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

        now = timezone.now()
        expires_at = now + timedelta(minutes=5)
        tmp_txn = f'TMP-{secrets.token_hex(12)}'

        order = PaymentOrder.objects.create(
            txn_ref=tmp_txn,
            amount_vnd=pkg.amount_vnd,
            capture_package=pkg,
            device=device,
            booth_id=booth_id,
            expires_at=expires_at,
            status=PaymentOrder.Status.PENDING,
            payment_method=PaymentOrder.PaymentMethod.PAYPAL,
        )
        order.txn_ref = str(order.pk)
        order.save(update_fields=['txn_ref', 'updated_at'])

        usd_amount = _vnd_to_usd(pkg.amount_vnd)
        description = f'Photobooth {pkg.code}'[:127]

        # Xây dựng return/cancel URL
        base_url = request.build_absolute_uri('/').rstrip('/')
        return_url = f'{base_url}/api/payments/paypal/return/?order_id={order.txn_ref}'
        cancel_url = f'{base_url}/api/payments/paypal/cancel/?order_id={order.txn_ref}'

        paypal_body = {
            'intent': 'CAPTURE',
            'purchase_units': [
                {
                    'reference_id': order.txn_ref,
                    'description': description,
                    'amount': {
                        'currency_code': 'USD',
                        'value': usd_amount,
                    },
                }
            ],
            'payment_source': {
                'paypal': {
                    'experience_context': {
                        'return_url': return_url,
                        'cancel_url': cancel_url,
                        'user_action': 'PAY_NOW',
                        'brand_name': 'Museum Photobooth',
                        'landing_page': 'NO_PREFERENCE',
                    }
                }
            },
        }

        try:
            resp = requests.post(
                f'{_paypal_base_url()}/v2/checkout/orders',
                json=paypal_body,
                headers=_paypal_headers(),
                timeout=15,
            )
            resp.raise_for_status()
            pp_data = resp.json()
        except requests.RequestException as e:
            order.delete()
            logger.exception('PayPal create order failed')
            detail = ''
            try:
                detail = e.response.json().get('message', '') if e.response else ''
            except Exception:
                pass
            return Response(
                {'detail': detail or str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        paypal_order_id = pp_data['id']
        approval_url = ''
        for link in pp_data.get('links', []):
            if link.get('rel') == 'payer-action':
                approval_url = link['href']
                break

        if not approval_url:
            # Fallback: look for 'approve' link
            for link in pp_data.get('links', []):
                if link.get('rel') == 'approve':
                    approval_url = link['href']
                    break

        order.paypal_order_id = paypal_order_id
        order.save(update_fields=['paypal_order_id', 'updated_at'])

        return Response(
            {
                'order_id': order.txn_ref,
                'paypal_order_id': paypal_order_id,
                'approval_url': approval_url,
                'amount_vnd': order.amount_vnd,
                'amount_usd': usd_amount,
                'expired_at': int(expires_at.timestamp() * 1000),
                'package': {
                    'id': pkg.id,
                    'code': pkg.code,
                    'name': pkg.name,
                    'print_count': pkg.print_count,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class PaypalReturnView(APIView):
    """
    GET /api/payments/paypal/return/?order_id=...&token=...&PayerID=...
    PayPal redirect về đây sau khi khách approve → auto capture → đánh dấu PAID.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        our_order_id = request.GET.get('order_id', '')
        order = PaymentOrder.objects.filter(txn_ref=our_order_id).first() if our_order_id else None

        if order and order.status == PaymentOrder.Status.PENDING and order.paypal_order_id:
            _capture_paypal_order(order)

        if order and order.status == PaymentOrder.Status.PAID:
            body = (
                '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Payment</title></head>'
                '<body style="font-family:sans-serif;text-align:center;padding:40px">'
                '<h2>✅ Payment Successful</h2>'
                f'<p>Order: {escape(our_order_id)}</p>'
                '<p>You can close this page and return to the photobooth.</p>'
                '</body></html>'
            )
        else:
            body = (
                '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Payment</title></head>'
                '<body style="font-family:sans-serif;text-align:center;padding:40px">'
                '<h2>⏳ Processing...</h2>'
                '<p>Please wait while we confirm your payment.</p>'
                '</body></html>'
            )
        from django.http import HttpResponse
        return HttpResponse(body, content_type='text/html; charset=utf-8')


class PaypalCancelView(APIView):
    """
    GET /api/payments/paypal/cancel/?order_id=...
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        body = (
            '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Payment</title></head>'
            '<body style="font-family:sans-serif;text-align:center;padding:40px">'
            '<h2>Payment Cancelled</h2>'
            '<p>You can close this page and return to the photobooth.</p>'
            '</body></html>'
        )
        from django.http import HttpResponse
        return HttpResponse(body, content_type='text/html; charset=utf-8')


# ── Capture + Sync helpers (used by PaymentStatusView too) ──────────────


def _capture_paypal_order(order: PaymentOrder) -> bool:
    """Gọi PayPal capture API. Trả True nếu capture thành công."""
    if not _paypal_configured() or not order.paypal_order_id:
        return False
    try:
        resp = requests.post(
            f'{_paypal_base_url()}/v2/checkout/orders/{order.paypal_order_id}/capture',
            headers=_paypal_headers(),
            json={},
            timeout=15,
        )
        data = resp.json()
        pp_status = data.get('status', '')

        if pp_status == 'COMPLETED':
            PaymentOrder.objects.filter(
                pk=order.pk,
                status=PaymentOrder.Status.PENDING,
            ).update(
                status=PaymentOrder.Status.PAID,
                paid_at=timezone.now(),
            )
            order.refresh_from_db()
            return True

        logger.info('PayPal capture status=%s for order %s', pp_status, order.txn_ref)
    except Exception:
        logger.exception('PayPal capture failed for order %s', order.txn_ref)
    return False


def sync_paypal_status(order: PaymentOrder) -> str | None:
    """
    Kiểm tra trạng thái đơn PayPal (GET order).
    Nếu APPROVED → auto capture. Nếu COMPLETED → đánh dấu PAID.
    Trả về PaymentOrder.Status mới nếu có thay đổi, hoặc None.
    """
    if not _paypal_configured() or not order.paypal_order_id:
        return None

    try:
        resp = requests.get(
            f'{_paypal_base_url()}/v2/checkout/orders/{order.paypal_order_id}',
            headers=_paypal_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        pp_status = data.get('status', '')

        if pp_status == 'COMPLETED':
            PaymentOrder.objects.filter(
                pk=order.pk,
                status=PaymentOrder.Status.PENDING,
            ).update(
                status=PaymentOrder.Status.PAID,
                paid_at=timezone.now(),
            )
            order.refresh_from_db()
            return PaymentOrder.Status.PAID

        if pp_status == 'APPROVED':
            # Khách đã approve → auto capture
            if _capture_paypal_order(order):
                return PaymentOrder.Status.PAID

        if pp_status in ('VOIDED', 'PAYER_ACTION_REQUIRED'):
            # Nothing to do — still pending from our perspective
            pass

    except Exception:
        logger.exception('PayPal sync failed for order %s', order.txn_ref)

    return None
