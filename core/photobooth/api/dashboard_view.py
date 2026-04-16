from __future__ import annotations

from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PaymentOrder, PhotoboothDevice

_VN_TZ = ZoneInfo('Asia/Ho_Chi_Minh')


class DashboardView(APIView):
    """
    GET /api/photobooth/cms/dashboard/

    Tổng quan doanh thu: hôm nay, tuần này, tháng này, tất cả.
    Biểu đồ 7 ngày gần nhất + đơn gần nhất + thống kê thiết bị.
    """

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())  # Monday
        month_start = today_start.replace(day=1)

        paid_qs = PaymentOrder.objects.filter(status=PaymentOrder.Status.PAID)

        def _agg(qs):
            r = qs.aggregate(total=Sum('amount_vnd'), count=Count('id'))
            return {'total': r['total'] or 0, 'count': r['count'] or 0}

        summary = {
            'today': _agg(paid_qs.filter(paid_at__gte=today_start)),
            'week': _agg(paid_qs.filter(paid_at__gte=week_start)),
            'month': _agg(paid_qs.filter(paid_at__gte=month_start)),
            'all': _agg(paid_qs),
        }

        # ── Biểu đồ 7 ngày gần nhất ──
        seven_days_ago = now - timedelta(days=7)
        chart_rows = (
            paid_qs
            .filter(paid_at__gte=seven_days_ago)
            .annotate(day=TruncDate('paid_at', tzinfo=_VN_TZ))
            .values('day')
            .annotate(total=Sum('amount_vnd'), count=Count('id'))
            .order_by('day')
        )
        chart = [
            {
                'date': str(r['day']),
                'label': r['day'].strftime('%d/%m'),
                'total': r['total'] or 0,
                'count': r['count'] or 0,
            }
            for r in chart_rows
        ]

        # ── Đơn thanh toán gần nhất (15 đơn) ──
        recent_orders = list(
            paid_qs
            .select_related('device', 'capture_package')
            .order_by('-paid_at')[:15]
            .values(
                'id', 'txn_ref', 'amount_vnd', 'payment_method',
                'paid_at', 'device__name', 'capture_package__name',
            )
        )
        orders_data = [
            {
                'id': o['id'],
                'txn_ref': o['txn_ref'],
                'amount': o['amount_vnd'],
                'method': o['payment_method'],
                'paid_at': o['paid_at'].isoformat() if o['paid_at'] else None,
                'device': o['device__name'] or '—',
                'package': o['capture_package__name'] or '—',
            }
            for o in recent_orders
        ]

        # ── Tổng thiết bị ──
        device_stats = {
            'total': PhotoboothDevice.objects.count(),
            'active': PhotoboothDevice.objects.filter(is_active=True).count(),
        }

        return Response({
            'summary': summary,
            'chart_7d': chart,
            'recent_orders': orders_data,
            'device_stats': device_stats,
        })
