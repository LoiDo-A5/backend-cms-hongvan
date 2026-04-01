from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from artwork.models import ShareLink
from artwork.serializers.share_link import (
    ShareLinkCreateSerializer,
    ShareLinkDetailSerializer,
    ShareLinkListSerializer,
    ShareLinkUpdateSerializer,
)


class ShareLinkViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ShareLinkCreateSerializer

    def get_queryset(self):
        return ShareLink.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ShareLinkListSerializer
        elif self.action in ['update', 'partial_update']:
            return ShareLinkUpdateSerializer
        elif self.action == 'retrieve':
            return ShareLinkDetailSerializer
        return ShareLinkCreateSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = ShareLinkCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        share_link = serializer.save(user=request.user)

        detail_serializer = ShareLinkDetailSerializer(share_link, context={'request': request})
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)
