from rest_framework import serializers, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.photobooth.models import PhotoboothSticker


class PhotoboothStickerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PhotoboothSticker
        fields = ['id', 'code', 'name', 'image', 'image_url', 'sort_order', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at', 'image_url']
        extra_kwargs = {'image': {'required': False, 'allow_null': True}}

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class StickerCrudView(APIView):
    """
    CMS CRUD sticker (admin only).
    GET  /api/photobooth/cms/stickers/       → list tất cả
    POST /api/photobooth/cms/stickers/       → tạo mới (multipart)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    PAGE_SIZE = 24

    def get(self, request):
        qs = PhotoboothSticker.objects.all().order_by('sort_order', 'id')
        total = qs.count()
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (ValueError, TypeError):
            page = 1
        offset = (page - 1) * self.PAGE_SIZE
        items = qs[offset:offset + self.PAGE_SIZE]
        data = PhotoboothStickerSerializer(items, many=True, context={'request': request}).data
        return Response({'total': total, 'page': page, 'page_size': self.PAGE_SIZE, 'results': data})

    def post(self, request):
        ser = PhotoboothStickerSerializer(data=request.data, context={'request': request})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)


class StickerDetailCrudView(APIView):
    """
    PUT    /api/photobooth/cms/stickers/<pk>/  → cập nhật (multipart)
    DELETE /api/photobooth/cms/stickers/<pk>/  → xoá
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAdminUser]

    def _get(self, pk):
        try:
            return PhotoboothSticker.objects.get(pk=pk)
        except PhotoboothSticker.DoesNotExist:
            return None

    def put(self, request, pk):
        obj = self._get(pk)
        if not obj:
            return Response({'detail': 'Không tìm thấy.'}, status=status.HTTP_404_NOT_FOUND)
        ser = PhotoboothStickerSerializer(obj, data=request.data, partial=True, context={'request': request})
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def delete(self, request, pk):
        obj = self._get(pk)
        if not obj:
            return Response({'detail': 'Không tìm thấy.'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
