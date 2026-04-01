from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from artwork.utils.mixin.share_link import ShareLinkValidateMixin
from artwork.serializers.share_link import (
    ShareLinkDetailSerializer,
    ShareLinkAccessSerializer,
)


class ShareLinkAccessAPIView(ShareLinkValidateMixin, GenericAPIView):
    permission_classes = []
    serializer_class = ShareLinkAccessSerializer

    def get(self, request, pk=None):
        password = request.query_params.get('password')
        share_link = self.validate_share_link(
            share_link_id=pk,
            request=request,
            password=password,
        )

        return Response({
            'share_link': ShareLinkDetailSerializer(share_link, context={'request': request}).data,
        })

    def post(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data.get('password')
        share_link = self.validate_share_link(
            share_link_id=pk,
            request=request,
            password=password,
        )

        return Response({
            'share_link': ShareLinkDetailSerializer(share_link, context={'request': request}).data,
        })
