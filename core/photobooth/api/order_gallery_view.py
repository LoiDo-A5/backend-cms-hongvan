from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import ImagePhotobooth, PaymentOrder


class OrderGalleryView(APIView):
    """
    GET /api/photobooth/gallery/<order_id>/

    Trả về danh sách ảnh theo đơn thanh toán.
    - Ưu tiên khớp ``txn_ref`` (ví dụ PB-20260404-abc123).
    - Nếu không có và ``order_id`` chỉ gồm chữ số → thử khớp ``PaymentOrder.pk`` (tiện dev / admin).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, order_id):
        order = PaymentOrder.objects.filter(txn_ref=order_id).first()
        if not order and order_id.isdigit():
            order = PaymentOrder.objects.filter(pk=int(order_id)).first()

        if not order:
            return Response(
                {'detail': f'Không tìm thấy đơn thanh toán "{order_id}".'},
                status=status.HTTP_404_NOT_FOUND,
            )

        images = ImagePhotobooth.objects.filter(payment_order=order).order_by(
            'round_index', 'photo_index', 'id',
        )

        data = []
        for img in images:
            data.append({
                'id': img.id,
                'round_index': img.round_index,
                'photo_index': img.photo_index,
                'image_url': request.build_absolute_uri(img.image.url) if img.image else None,
                'created_at': img.created_at.isoformat(),
            })

        return Response({
            'order_id': order.txn_ref,
            'status': order.status,
            'total_images': len(data),
            'images': data,
        })
