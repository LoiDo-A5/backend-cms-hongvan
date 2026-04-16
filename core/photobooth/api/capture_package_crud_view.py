from rest_framework import status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import CapturePackage
from core.photobooth.serializers.capture_package import (
    CapturePackageWriteSerializer,
)


class CapturePackageCrudView(APIView):
    """
    CMS CRUD cho gói chụp (admin only).

    GET  /api/photobooth/cms/packages/           → list tất cả (kể cả inactive)
    POST /api/photobooth/cms/packages/           → tạo mới
    """

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = CapturePackage.objects.all().order_by('sort_order', 'id')
        serializer = CapturePackageWriteSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CapturePackageWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CapturePackageDetailCrudView(APIView):
    """
    PUT    /api/photobooth/cms/packages/<pk>/  → cập nhật
    DELETE /api/photobooth/cms/packages/<pk>/  → xoá
    """

    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    def put(self, request, pk):
        try:
            obj = CapturePackage.objects.get(pk=pk)
        except CapturePackage.DoesNotExist:
            return Response({'detail': 'Không tìm thấy.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CapturePackageWriteSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            obj = CapturePackage.objects.get(pk=pk)
        except CapturePackage.DoesNotExist:
            return Response({'detail': 'Không tìm thấy.'}, status=status.HTTP_404_NOT_FOUND)

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
