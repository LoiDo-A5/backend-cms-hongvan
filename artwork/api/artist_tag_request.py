from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination

from artwork.models import ArtistTagRequest
from artwork.serializers.artist_tag_request import ReviewArtistTagRequestSerializer, ApproveArtistTagRequestSerializer
from artwork.serializers.artist_tag_request import RejectArtistTagRequestSerializer
from artwork.utils.const import STATUS_REQUEST
from core.accounts.models.user import USER_ROLE


class ArtistTagPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        data_response = {
            'page_size': self.page_size,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        }
        return Response(data_response)


class ArtistTagRequestViewSet(ModelViewSet):
    queryset = ArtistTagRequest.objects.all()
    serializer_class = RejectArtistTagRequestSerializer
    pagination_class = ArtistTagPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = {
        'artwork': ['exact'],
        'status': ['in'],
    }

    def get_queryset(self):
        user = self.request.user
        user_role = user.role

        queryset = super().get_queryset()

        role_filter = {
            USER_ROLE.COLLECTOR: {'request_by': user},
            USER_ROLE.ARTIST: {'request_to': user},
        }

        if self.action == 'list' and user_role in role_filter:
            queryset = queryset.filter(**role_filter[user_role])

        return queryset.order_by('-id')

    def get_serializer_class(self):
        if self.action in ['review_artist_tag_request', 'list']:
            return ReviewArtistTagRequestSerializer
        if self.action == 'approve_artist_tag_request':
            return ApproveArtistTagRequestSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['get'])
    def review_artist_tag_request(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        artwork = get_object_or_404(self.get_queryset(), id=pk)
        serializer = self.get_serializer(artwork)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def approve_artist_tag_request(self, request, *args, **kwargs):
        instance = self.get_object()
        has_permission_approve = instance.request_to == self.request.user

        if not has_permission_approve:
            raise PermissionDenied('You do not have permission to approve this request.')

        exist_approve_request_tag = ArtistTagRequest.objects.filter(artwork=instance.artwork,
                                                                    status=STATUS_REQUEST.REQUEST_APPROVED) \
                                                            .exists()

        if exist_approve_request_tag:
            raise ValidationError('An approved request tag for this artwork already exists.')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.process()

        instance.status = STATUS_REQUEST.REQUEST_APPROVED
        instance.save()

        ArtistTagRequest.objects.filter(artwork=instance.artwork) \
                                .exclude(id=instance.id) \
                                .update(status=STATUS_REQUEST.REQUEST_CANCELED)

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject_artist_tag_request(self, request, *args, **kwargs):
        instance = self.get_object()
        has_permission_approve = instance.request_to == self.request.user

        if not has_permission_approve:
            raise PermissionDenied('You do not have permission to approve this request.')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.process(instance)

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def resend_artist_tag_request(self, request, *args, **kwargs):
        instance = self.get_object()
        has_permission_approve = instance.request_by == self.request.user

        if not has_permission_approve:
            raise PermissionDenied('You do not have permission to approve this request.')

        instance.status = STATUS_REQUEST.REQUEST_RECEIVED
        instance.save()

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel_artist_tag_request(self, request, *args, **kwargs):
        instance = self.get_object()
        has_permission_approve = instance.request_by == self.request.user

        if not has_permission_approve:
            raise PermissionDenied('You do not have permission to cancel this request.')

        instance.status = STATUS_REQUEST.REQUEST_CANCELED
        instance.save()

        artwork = instance.artwork
        artwork.artist_name = ''
        artwork.save()

        return Response(status=status.HTTP_200_OK)
