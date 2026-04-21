"""
PayPal REST API v2 — tạo đơn thanh toán, capture, kiểm tra trạng thái.
"""
from __future__ import annotations

import logging
import secrets
from datetime import timedelta

import requests
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.utils.html import escape
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.payments.models import PaymentOrder

logger = logging.getLogger(__name__)

_access_token_cache: dict = {}


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
    """Quy đổi VND → USD. PayPal không hỗ trợ VND trực tiếp."""
    rate = 25_500
    usd = amount_vnd / rate
    return f'{usd:.2f}'


class PaypalCreatePaymentView(APIView):
    """
    POST /api/payments/paypal/create/
    Body: { "amount_vnd": 50000, "description": "...", "extra_data": {} }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not _paypal_configured():
            return Response(
                {'detail': 'PayPal chưa cấu hình (PAYPAL_CLIENT_ID, PAYPAL_SECRET_KEY).'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        amount_vnd = request.data.get('amount_vnd')
        description = (request.data.get('description') or '')[:255]
        extra_data = request.data.get('extra_data') or {}

        if not amount_vnd or not isinstance(amount_vnd, int) or amount_vnd <= 0:
            return Response({'detail': 'amount_vnd là số nguyên dương.'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        expires_at = now + timedelta(minutes=15)
        tmp_txn = f'TMP-{secrets.token_hex(12)}'

        order = PaymentOrder.objects.create(
            txn_ref=tmp_txn,
            amount_vnd=amount_vnd,
            description=description,
            extra_data=extra_data,
            expires_at=expires_at,
            status=PaymentOrder.Status.PENDING,
            payment_method=PaymentOrder.PaymentMethod.PAYPAL,
        )
        order.txn_ref = str(order.pk)
        order.save(update_fields=['txn_ref', 'updated_at'])

        usd_amount = _vnd_to_usd(amount_vnd)
        paypal_description = (description or f'Order {order.txn_ref}')[:127]

        base_url = request.build_absolute_uri('/').rstrip('/')
        return_url = f'{base_url}/api/payments/paypal/return/?order_id={order.txn_ref}'
        cancel_url = f'{base_url}/api/payments/paypal/cancel/?order_id={order.txn_ref}'

        paypal_body = {
            'intent': 'CAPTURE',
            'purchase_units': [
                {
                    'reference_id': order.txn_ref,
                    'description': paypal_description,
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
            return Response({'detail': detail or str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        paypal_order_id = pp_data['id']
        approval_url = ''
        for link in pp_data.get('links', []):
            if link.get('rel') == 'payer-action':
                approval_url = link['href']
                break
        if not approval_url:
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
            },
            status=status.HTTP_201_CREATED,
        )


class PaypalReturnView(APIView):
    """GET /api/payments/paypal/return/ — PayPal redirect sau khi approve."""

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
                '<p>You can close this page.</p></body></html>'
            )
        else:
            body = (
                '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Payment</title></head>'
                '<body style="font-family:sans-serif;text-align:center;padding:40px">'
                '<h2>⏳ Processing...</h2>'
                '<p>Please wait while we confirm your payment.</p></body></html>'
            )
        return HttpResponse(body, content_type='text/html; charset=utf-8')


class PaypalCancelView(APIView):
    """GET /api/payments/paypal/cancel/"""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        body = (
            '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Payment</title></head>'
            '<body style="font-family:sans-serif;text-align:center;padding:40px">'
            '<h2>Payment Cancelled</h2>'
            '<p>You can close this page.</p></body></html>'
        )
        return HttpResponse(body, content_type='text/html; charset=utf-8')


def _capture_paypal_order(order: PaymentOrder) -> bool:
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
        if data.get('status') == 'COMPLETED':
            PaymentOrder.objects.filter(pk=order.pk, status=PaymentOrder.Status.PENDING).update(
                status=PaymentOrder.Status.PAID,
                paid_at=timezone.now(),
            )
            order.refresh_from_db()
            return True
        logger.info('PayPal capture status=%s for order %s', data.get('status'), order.txn_ref)
    except Exception:
        logger.exception('PayPal capture failed for order %s', order.txn_ref)
    return False


def sync_paypal_status(order: PaymentOrder) -> str | None:
    if not _paypal_configured() or not order.paypal_order_id:
        return None
    try:
        resp = requests.get(
            f'{_paypal_base_url()}/v2/checkout/orders/{order.paypal_order_id}',
            headers=_paypal_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        pp_status = resp.json().get('status', '')

        if pp_status == 'COMPLETED':
            PaymentOrder.objects.filter(pk=order.pk, status=PaymentOrder.Status.PENDING).update(
                status=PaymentOrder.Status.PAID, paid_at=timezone.now())
            order.refresh_from_db()
            return PaymentOrder.Status.PAID

        if pp_status == 'APPROVED':
            if _capture_paypal_order(order):
                return PaymentOrder.Status.PAID

    except Exception:
        logger.exception('PayPal sync failed for order %s', order.txn_ref)
    return None
