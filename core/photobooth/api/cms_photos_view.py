from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import ImagePhotobooth


class CmsPhotosView(APIView):
    """
    CMS: Danh sách ảnh photobooth (read-only, admin only).
    GET /api/photobooth/cms/photos/
        ?page=1
        &device_id=<int>
        &status=paid|pending|expired|failed
        &date=YYYY-MM-DD       (lọc theo ngày tạo đơn, dạng created_at__date)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    PAGE_SIZE = 48

    def get(self, request):
        qs = ImagePhotobooth.objects.select_related(
            'payment_order__device', 'payment_order__capture_package'
        ).order_by('-id')

        # Filter by device
        device_id = request.query_params.get('device_id')
        if device_id and device_id.isdigit():
            qs = qs.filter(payment_order__device_id=int(device_id))

        # Filter by order status
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(payment_order__status=status_filter)

        # Filter by date (YYYY-MM-DD)
        date_filter = request.query_params.get('date')
        if date_filter:
            qs = qs.filter(created_at__date=date_filter)

        total = qs.count()

        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (ValueError, TypeError):
            page = 1

        offset = (page - 1) * self.PAGE_SIZE
        items = qs[offset: offset + self.PAGE_SIZE]

        data = []
        for img in items:
            order = img.payment_order
            data.append({
                'id': img.id,
                'image_url': request.build_absolute_uri(img.image.url) if img.image else None,
                'round_index': img.round_index,
                'photo_index': img.photo_index,
                'created_at': img.created_at.isoformat(),
                'order': {
                    'id': order.id,
                    'txn_ref': order.txn_ref,
                    'status': order.status,
                    'payment_method': order.payment_method,
                    'amount_vnd': order.amount_vnd,
                },
                'device_name': order.device.name if order.device else order.booth_id or '',
                'package_name': order.capture_package.name if order.capture_package else '',
            })

        return Response({
            'total': total,
            'page': page,
            'page_size': self.PAGE_SIZE,
            'results': data,
        })
