from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from core.photobooth.models import CapturePackage
from core.photobooth.serializers import CapturePackageSerializer


class CapturePackageListView(ListAPIView):
    """
    GET /api/photobooth/packages/
    Danh sách gói đang bật — dùng cho màn 'Chọn gói chụp' trên booth.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CapturePackageSerializer

    def get_queryset(self):
        return CapturePackage.objects.filter(is_active=True).order_by(
            'sort_order', 'id'
        )
