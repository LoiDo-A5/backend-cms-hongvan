import django_filters
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from artwork.models import ShareLink
from artwork.serializers.manage_share_link import ExtendShareLinkSerializer, ManageShareLinkSerializer


class ManageShareLinkPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'page_size': self.get_page_size(self.request),
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })


class ManageShareLinkFilter(filters.FilterSet):
    share_type = django_filters.CharFilter(field_name='share_type', lookup_expr='exact')
    is_share_all = django_filters.BooleanFilter(field_name='is_share_all')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    recipient_type = django_filters.CharFilter(field_name='recipient_type', lookup_expr='exact')
    expiration_type = django_filters.CharFilter(field_name='expiration_type', lookup_expr='exact')
    created_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = ShareLink
        fields = [
            'share_type', 'is_share_all', 'is_active',
            'recipient_type', 'expiration_type',
        ]


class ManageShareLinkListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ManageShareLinkSerializer
    pagination_class = ManageShareLinkPagination
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = ManageShareLinkFilter
    search_fields = ('title', 'description')
    ordering_fields = (
        'created_at', 'expires_at', 'access_count', 'title', 'updated_at',
    )
    ordering = ('-created_at',)

    def get_queryset(self):
        queryset = ShareLink.objects.filter(user=self.request.user)

        tab = self.request.query_params.get('tab')

        if tab == 'selected_artworks':
            queryset = queryset.filter(share_type='artwork')
        else:
            # tab=my_page (default): all share links except type artwork
            queryset = queryset.exclude(share_type='artwork')

        return queryset


class RevokeShareLinkAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        share_link_id = self.kwargs.get('pk')
        return ShareLink.objects.get(id=share_link_id, user=self.request.user)

    def delete(self, request, pk=None):
        try:
            share_link = self.get_object()
        except ShareLink.DoesNotExist:
            return Response(
                {'detail': 'Share link not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        share_link.delete()

        return Response(
            {'message': 'Share link revoked successfully.'},
            status=status.HTTP_200_OK,
        )


class ExtendShareLinkAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExtendShareLinkSerializer

    def get_object(self):
        share_link_id = self.kwargs.get('pk')
        return ShareLink.objects.get(id=share_link_id, user=self.request.user)

    def patch(self, request, pk=None):
        try:
            share_link = self.get_object()
        except ShareLink.DoesNotExist:
            return Response(
                {'detail': 'Share link not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        share_link.expiration_type = validated['expiration_type']
        share_link.expires_at = validated.get('expires_at')
        share_link.is_active = True
        share_link.save(update_fields=['expiration_type', 'expires_at', 'is_active', 'updated_at'])

        return Response(
            {'message': 'Share link extended successfully.'},
            status=status.HTTP_200_OK,
        )
