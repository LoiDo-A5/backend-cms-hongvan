from __future__ import annotations

import logging
from datetime import timedelta
from datetime import timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.html import escape
from django.utils import timezone
from django.views import View
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import CapturePackage, PaymentOrder
from core.photobooth.vnpay import (
    build_payment_secure_hash,
    build_payment_url,
    normalize_order_info_ascii,
    verify_callback_secure_hash,
)

logger = logging.getLogger(__name__)

# VNPAY: vnp_CreateDate / vnp_ExpireDate là giờ GMT+7 (tài liệu PAY), không dùng giờ UTC của Django.
_VN_TZ = ZoneInfo('Asia/Ho_Chi_Minh')


def _now_vietnam():
    return timezone.now().astimezone(_VN_TZ)


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def _vnpay_configured() -> bool:
    return bool(
        getattr(settings, 'VNPAY_TMN_CODE', '')
        and getattr(settings, 'VNPAY_HASH_SECRET', '')
        and getattr(settings, 'VNPAY_RETURN_URL', ''),
    )


class VnpayCreatePaymentView(APIView):
    """
    POST /api/payments/vnpay/create/
    Body JSON: { "package_id": 1 } hoặc { "package_code": "economy" }, optional "booth_id"
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not _vnpay_configured():
            return Response(
                {'detail': 'VNPAY chưa cấu hình (VNPAY_TMN_CODE, VNPAY_HASH_SECRET, VNPAY_RETURN_URL).'},
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
        # Lưu DB theo UTC (USE_TZ) — cùng thời điểm với expires_vn
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

        order_info = normalize_order_info_ascii(
            f'Thanh toan goi {pkg.name} ma {txn_ref}'
        )
        create_date = now_vn.strftime('%Y%m%d%H%M%S')
        expire_date = expires_vn.strftime('%Y%m%d%H%M%S')

        params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': settings.VNPAY_TMN_CODE,
            'vnp_Amount': str(order.amount_vnd * 100),
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': txn_ref,
            'vnp_OrderInfo': order_info,
            'vnp_OrderType': 'other',
            'vnp_Locale': 'vn',
            'vnp_ReturnUrl': settings.VNPAY_RETURN_URL,
            'vnp_IpAddr': _client_ip(request),
            'vnp_CreateDate': create_date,
            'vnp_ExpireDate': expire_date,
        }
        bank = getattr(settings, 'VNPAY_DEFAULT_BANK_CODE', '') or ''
        if bank:
            params['vnp_BankCode'] = bank

        secure = build_payment_secure_hash(params, settings.VNPAY_HASH_SECRET)
        params['vnp_SecureHash'] = secure

        payment_url = build_payment_url(settings.VNPAY_PAYMENT_URL, params)

        return Response(
            {
                'payment_url': payment_url,
                'order_id': txn_ref,
                'amount_vnd': order.amount_vnd,
                'expired_at': int(expires_at_utc.timestamp() * 1000),
                'package': {'id': pkg.id, 'code': pkg.code, 'name': pkg.name},
            },
            status=status.HTTP_201_CREATED,
        )


def _make_txn_ref() -> str:
    import secrets

    # Cùng múi giờ với vnp_CreateDate / vnp_ExpireDate (GMT+7). Không dùng TIME_ZONE Django (thường UTC) — tránh PB-...14:02 trong khi CreateDate là 21:02.
    ts = _now_vietnam().strftime('%Y%m%d%H%M%S')
    suf = secrets.token_hex(4)
    return f'PB-{ts}-{suf}'


class VnpayIpnView(View):
    """GET /api/payments/vnpay/ipn/ — VNPAY server-to-server."""

    def get(self, request, *args, **kwargs):
        if not _vnpay_configured():
            return JsonResponse({'RspCode': '99', 'Message': 'VNPAY not configured'}, status=503)

        data = {k: v for k, v in request.GET.items() if k.startswith('vnp_')}
        secure_hash = data.pop('vnp_SecureHash', None)
        data.pop('vnp_SecureHashType', None)

        if not verify_callback_secure_hash(data, settings.VNPAY_HASH_SECRET, secure_hash):
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
    """
    GET /api/payments/vnpay/return/ — redirect trình duyệt; chỉ hiển thị, không cập nhật đơn.
    """

    def get(self, request, *args, **kwargs):
        data = {k: v for k, v in request.GET.items() if k.startswith('vnp_')}
        secure_hash = data.pop('vnp_SecureHash', None)
        data.pop('vnp_SecureHashType', None)

        ok_sig = False
        if _vnpay_configured():
            ok_sig = verify_callback_secure_hash(data, settings.VNPAY_HASH_SECRET, secure_hash)

        rc = data.get('vnp_ResponseCode', '')
        txn = data.get('vnp_TxnRef', '')
        if ok_sig and rc == '00':
            body = (
                '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Thanh toán</title></head>'
                '<body><p>Giao dịch thành công.</p>'
                f'<p>Mã đơn: {escape(txn)}</p>'
                '<p>Bạn có thể đóng trang này và quay lại photobooth.</p></body></html>'
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
    """GET /api/payments/status/<order_id>/ — poll cho Electron."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, order_id, *args, **kwargs):
        order = PaymentOrder.objects.filter(txn_ref=order_id).first()
        if not order:
            return Response({'status': 'NotFound', 'order_id': order_id}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        st = order.status
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

        payload = {
            'order_id': order.txn_ref,
            'status': api_status,
            'amount_vnd': order.amount_vnd,
            'transaction_no': order.vnp_transaction_no or None,
            'paid_at': order.paid_at.isoformat() if order.paid_at else None,
        }
        return Response(payload)
