from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PaymentOrder


class OrderListView(APIView):
    """
    CMS: Danh sách đơn thanh toán (read-only, admin only).
    GET /api/photobooth/cms/orders/?status=paid&page=1
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = PaymentOrder.objects.select_related('capture_package', 'device').order_by('-id')

        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        method_filter = request.query_params.get('method')
        if method_filter:
            qs = qs.filter(payment_method=method_filter)

        # Simple pagination: 50 per page
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (ValueError, TypeError):
            page = 1
        page_size = 50
        offset = (page - 1) * page_size
        total = qs.count()
        qs = qs[offset: offset + page_size]

        data = []
        for o in qs:
            data.append({
                'id': o.id,
                'txn_ref': o.txn_ref,
                'amount_vnd': o.amount_vnd,
                'status': o.status,
                'payment_method': o.payment_method,
                'package_name': o.capture_package.name if o.capture_package else '',
                'device_name': o.device.name if o.device else '',
                'booth_id': o.booth_id,
                'payos_order_code': o.payos_order_code,
                'created_at': o.created_at.isoformat(),
                'paid_at': o.paid_at.isoformat() if o.paid_at else None,
                'expires_at': o.expires_at.isoformat(),
            })
        return Response({'total': total, 'page': page, 'page_size': page_size, 'results': data})
