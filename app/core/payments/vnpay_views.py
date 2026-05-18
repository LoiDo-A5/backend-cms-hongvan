from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.payments.models import PaymentOrder
from core.payments.vnpay import (
    build_payment_secure_hash,
    build_payment_url,
    normalize_order_info_ascii,
    verify_callback_secure_hash,
)

logger = logging.getLogger(__name__)

_VN_TZ = ZoneInfo('Asia/Ho_Chi_Minh')


def _now_vietnam():
    return timezone.now().astimezone(_VN_TZ)


def _client_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def _vnpay_configured() -> bool:
    return bool(
        (getattr(settings, 'VNPAY_TMN_CODE', '') or '').strip()
        and (getattr(settings, 'VNPAY_HASH_SECRET', '') or '').strip()
        and (getattr(settings, 'VNPAY_PAYMENT_URL', '') or '').strip()
        and (getattr(settings, 'VNPAY_RETURN_URL', '') or '').strip()
    )


class VnpayCreatePaymentView(APIView):
    """
    POST /api/payments/vnpay/create/
    Body: { "amount_vnd": 50000, "description": "...", "extra_data": {} }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not _vnpay_configured():
            return Response(
                {'detail': 'VNPAY chưa cấu hình (VNPAY_TMN_CODE, VNPAY_HASH_SECRET, VNPAY_PAYMENT_URL, VNPAY_RETURN_URL).'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        amount_vnd = request.data.get('amount_vnd')
        description = (request.data.get('description') or '')[:255]
        extra_data = request.data.get('extra_data') or {}

        if not amount_vnd or not isinstance(amount_vnd, int) or amount_vnd <= 0:
            return Response({'detail': 'amount_vnd là số nguyên dương.'}, status=status.HTTP_400_BAD_REQUEST)

        now_vn = _now_vietnam()
        expires_vn = now_vn + timedelta(minutes=15)
        expires_at_utc = expires_vn.astimezone(tz=None)

        txn_ref = _make_txn_ref()
        order = PaymentOrder.objects.create(
            txn_ref=txn_ref,
            amount_vnd=amount_vnd,
            description=description,
            extra_data=extra_data,
            expires_at=expires_at_utc,
            status=PaymentOrder.Status.PENDING,
            payment_method=PaymentOrder.PaymentMethod.VNPAY,
        )

        tmn_code = settings.VNPAY_TMN_CODE.strip()
        hash_secret = settings.VNPAY_HASH_SECRET.strip()
        create_date = now_vn.strftime('%Y%m%d%H%M%S')
        expire_date = expires_vn.strftime('%Y%m%d%H%M%S')

        order_info = normalize_order_info_ascii(description or f'Order {txn_ref}')
        params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': tmn_code,
            'vnp_Amount': order.amount_vnd * 100,
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': txn_ref,
            'vnp_OrderInfo': order_info,
            'vnp_OrderType': 'other',
            'vnp_Locale': 'vn',
            'vnp_ReturnUrl': settings.VNPAY_RETURN_URL.strip(),
            'vnp_IpAddr': _client_ip(request),
            'vnp_CreateDate': create_date,
            'vnp_ExpireDate': expire_date,
        }
        bank = getattr(settings, 'VNPAY_DEFAULT_BANK_CODE', '') or ''
        if bank:
            params['vnp_BankCode'] = bank

        secure = build_payment_secure_hash(params, hash_secret)
        params['vnp_SecureHash'] = secure

        payment_url = build_payment_url(settings.VNPAY_PAYMENT_URL, params)

        return Response(
            {
                'payment_url': payment_url,
                'order_id': txn_ref,
                'amount_vnd': order.amount_vnd,
                'expired_at': int(expires_at_utc.timestamp() * 1000),
            },
            status=status.HTTP_201_CREATED,
        )


def _make_txn_ref() -> str:
    import secrets as _secrets
    ts = _now_vietnam().strftime('%Y%m%d%H%M%S')
    suf = _secrets.token_hex(4)
    return f'PAY-{ts}-{suf}'


class VnpayIpnView(View):
    """GET /api/payments/vnpay/ipn/ — VNPAY server-to-server IPN."""

    def get(self, request, *args, **kwargs):
        if not _vnpay_configured():
            return JsonResponse({'RspCode': '99', 'Message': 'VNPAY not configured'}, status=503)

        data = {k: v for k, v in request.GET.items() if k.startswith('vnp_')}
        secure_hash = data.pop('vnp_SecureHash', None)
        data.pop('vnp_SecureHashType', None)

        if not data or not secure_hash:
            return JsonResponse({'RspCode': '99', 'Message': 'Thiếu tham số VNPAY.'})

        if not verify_callback_secure_hash(data, (settings.VNPAY_HASH_SECRET or '').strip(), secure_hash):
            logger.warning('VNPAY IPN invalid signature: %s', request.GET)
            return JsonResponse({'RspCode': '97', 'Message': 'Invalid signature'})

        txn_ref = data.get('vnp_TxnRef')
        if not txn_ref:
            return JsonResponse({'RspCode': '99', 'Message': 'Invalid request'})

        order = PaymentOrder.objects.filter(txn_ref=txn_ref).first()
        if not order:
            return JsonResponse({'RspCode': '01', 'Message': 'Order not found'})

        try:
            vnp_amount = int(data.get('vnp_Amount', '0'))
        except ValueError:
            return JsonResponse({'RspCode': '04', 'Message': 'invalid amount'})

        if vnp_amount != order.amount_vnd * 100:
            return JsonResponse({'RspCode': '04', 'Message': 'invalid amount'})

        if order.status == PaymentOrder.Status.PAID:
            return JsonResponse({'RspCode': '02', 'Message': 'Order already confirmed'})

        if timezone.now() > order.expires_at and order.status == PaymentOrder.Status.PENDING:
            order.status = PaymentOrder.Status.EXPIRED
            order.save(update_fields=['status', 'updated_at'])
            return JsonResponse({'RspCode': '01', 'Message': 'Order expired'})

        rc = data.get('vnp_ResponseCode', '')
        ts = data.get('vnp_TransactionStatus', '')
        vnp_txn = data.get('vnp_TransactionNo', '')

        order.vnp_response_code = rc[:8]
        order.vnp_transaction_status = ts[:8]
        order.vnp_transaction_no = vnp_txn[:32]

        if rc == '00' and ts == '00':
            order.status = PaymentOrder.Status.PAID
            order.paid_at = timezone.now()
        else:
            order.status = PaymentOrder.Status.FAILED

        order.save()
        return JsonResponse({'RspCode': '00', 'Message': 'Confirm Success'})


class VnpayReturnView(View):
    """GET /api/payments/vnpay/return/ — redirect trình duyệt."""

    def get(self, request, *args, **kwargs):
        data = {k: v for k, v in request.GET.items() if k.startswith('vnp_')}
        secure_hash = data.pop('vnp_SecureHash', None)
        data.pop('vnp_SecureHashType', None)

        ok_sig = False
        if _vnpay_configured():
            ok_sig = verify_callback_secure_hash(
                data, (settings.VNPAY_HASH_SECRET or '').strip(), secure_hash
            )

        rc = data.get('vnp_ResponseCode', '')
        txn = data.get('vnp_TxnRef', '')
        if ok_sig and rc == '00':
            body = (
                '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Thanh toán</title></head>'
                '<body><p>Giao dịch thành công.</p>'
                f'<p>Mã đơn: {escape(txn)}</p>'
                '<p>Bạn có thể đóng trang này.</p></body></html>'
            )
        elif ok_sig:
            body = (
                '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Thanh toán</title></head>'
                '<body><p>Giao dịch chưa thành công hoặc đã hủy.</p>'
                f'<p>Mã lỗi: {escape(rc)}</p></body></html>'
            )
        else:
            body = (
                '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Thanh toán</title></head>'
                '<body><p>Không xác thực được dữ liệu trả về.</p></body></html>'
            )
        return HttpResponse(body, content_type='text/html; charset=utf-8')


class PaymentStatusView(APIView):
    """GET /api/payments/status/<order_id>/ — poll trạng thái đơn."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, order_id, *args, **kwargs):
        order = PaymentOrder.objects.filter(txn_ref=order_id).first()
        if not order:
            return Response({'status': 'NotFound', 'order_id': order_id}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        st = order.status

        # payOS fallback
        if st == PaymentOrder.Status.PENDING and order.payos_order_code:
            st = self._sync_payos_status(order, now) or st

        # PayPal fallback
        if st == PaymentOrder.Status.PENDING and order.paypal_order_id:
            st = self._sync_paypal_status(order) or st

        if st == PaymentOrder.Status.PENDING and now > order.expires_at:
            PaymentOrder.objects.filter(pk=order.pk, status=PaymentOrder.Status.PENDING).update(
                status=PaymentOrder.Status.EXPIRED
            )
            st = PaymentOrder.Status.EXPIRED

        api_status = {
            PaymentOrder.Status.PAID: 'Paid',
            PaymentOrder.Status.FAILED: 'Failed',
            PaymentOrder.Status.EXPIRED: 'Expired',
            PaymentOrder.Status.PENDING: 'Pending',
        }.get(st, 'Pending')

        return Response({
            'order_id': order.txn_ref,
            'status': api_status,
            'amount_vnd': order.amount_vnd,
            'description': order.description,
            'transaction_no': order.vnp_transaction_no or None,
            'paid_at': order.paid_at.isoformat() if order.paid_at else None,
            'extra_data': order.extra_data,
        })

    @staticmethod
    def _sync_payos_status(order, now):
        try:
            from core.payments.payos_views import _get_payos_client
            client = _get_payos_client()
            info = client.getPaymentLinkInformation(int(order.payos_order_code))
            payos_status = getattr(info, 'status', '') or ''

            if payos_status == 'PAID':
                ref = str(getattr(info, 'id', '') or '')[:64]
                PaymentOrder.objects.filter(pk=order.pk, status=PaymentOrder.Status.PENDING).update(
                    status=PaymentOrder.Status.PAID, paid_at=now,
                    vnp_transaction_no=ref, vnp_response_code='00', vnp_transaction_status='00',
                )
                order.refresh_from_db()
                return PaymentOrder.Status.PAID
            if payos_status == 'CANCELLED':
                PaymentOrder.objects.filter(pk=order.pk, status=PaymentOrder.Status.PENDING).update(
                    status=PaymentOrder.Status.FAILED)
                order.refresh_from_db()
                return PaymentOrder.Status.FAILED
            if payos_status == 'EXPIRED':
                PaymentOrder.objects.filter(pk=order.pk, status=PaymentOrder.Status.PENDING).update(
                    status=PaymentOrder.Status.EXPIRED)
                order.refresh_from_db()
                return PaymentOrder.Status.EXPIRED
        except Exception as exc:
            logger.debug('payOS status check failed for order %s: %s', order.pk, exc)
        return None

    @staticmethod
    def _sync_paypal_status(order):
        try:
            from core.payments.paypal_views import sync_paypal_status
            return sync_paypal_status(order)
        except Exception as exc:
            logger.debug('PayPal status check failed for order %s: %s', order.pk, exc)
        return None
