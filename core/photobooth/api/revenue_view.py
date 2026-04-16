from __future__ import annotations

from datetime import date, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PaymentOrder, PhotoboothDevice

_VN_TZ = ZoneInfo('Asia/Ho_Chi_Minh')


class RevenueView(APIView):
    """
    GET /api/photobooth/cms/revenue/?period=day|week|month&days=30&device_id=<int>

    Trả về doanh thu (chỉ đơn paid) tổng hợp theo ngày/tuần/tháng,
    có thể lọc theo thiết bị.
    """

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        period = request.query_params.get('period', 'day')  # day | week | month
        days = min(int(request.query_params.get('days', '30') or '30'), 365)
        device_id = request.query_params.get('device_id')  # PhotoboothDevice.pk

        now = timezone.now()
        since = now - timedelta(days=days)

        qs = PaymentOrder.objects.filter(
            status=PaymentOrder.Status.PAID,
            paid_at__gte=since,
        )
        if device_id:
            qs = qs.filter(device_id=device_id)

        # ── Tổng hợp ──
        trunc_fn = {
            'day': TruncDate('paid_at', tzinfo=_VN_TZ),
            'week': TruncWeek('paid_at', tzinfo=_VN_TZ),
            'month': TruncMonth('paid_at', tzinfo=_VN_TZ),
        }.get(period, TruncDate('paid_at', tzinfo=_VN_TZ))

        rows = (
            qs
            .annotate(bucket=trunc_fn)
            .values('bucket')
            .annotate(
                total=Sum('amount_vnd'),
                count=Count('id'),
            )
            .order_by('bucket')
        )

        chart = []
        for r in rows:
            b = r['bucket']
            label = b.strftime('%d/%m/%Y') if isinstance(b, date) else str(b)[:10]
            chart.append({
                'date': str(b)[:10] if b else None,
                'label': label,
                'total': r['total'] or 0,
                'count': r['count'] or 0,
            })

        # ── Tổng kết (summary) ──
        summary = qs.aggregate(
            total_revenue=Sum('amount_vnd'),
            total_orders=Count('id'),
        )

        # ── Doanh thu theo thiết bị ──
        by_device = (
            qs
            .filter(device__isnull=False)
            .values('device_id', 'device__name', 'device__device_id')
            .annotate(
                total=Sum('amount_vnd'),
                count=Count('id'),
            )
            .order_by('-total')
        )

        devices_data = [
            {
                'device_pk': d['device_id'],
                'device_name': d['device__name'] or d['device__device_id'] or f'ID {d["device_id"]}',
                'total': d['total'] or 0,
                'count': d['count'] or 0,
            }
            for d in by_device
        ]

        # ── Doanh thu theo phương thức thanh toán ──
        by_method = (
            qs
            .values('payment_method')
            .annotate(
                total=Sum('amount_vnd'),
                count=Count('id'),
            )
            .order_by('-total')
        )

        methods_data = [
            {
                'method': m['payment_method'],
                'total': m['total'] or 0,
                'count': m['count'] or 0,
            }
            for m in by_method
        ]

        # ── Danh sách thiết bị (cho dropdown filter) ──
        all_devices = list(
            PhotoboothDevice.objects.filter(is_active=True)
            .values_list('id', 'name')
            .order_by('name')
        )

        return Response({
            'period': period,
            'days': days,
            'device_id': int(device_id) if device_id else None,
            'summary': {
                'total_revenue': summary['total_revenue'] or 0,
                'total_orders': summary['total_orders'] or 0,
            },
            'chart': chart,
            'by_device': devices_data,
            'by_method': methods_data,
            'devices': [{'id': d[0], 'name': d[1]} for d in all_devices],
        })
