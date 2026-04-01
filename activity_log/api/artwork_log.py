from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from activity_log.models import ArtworkLog
from activity_log.serializers.artwork_log import ArtworkLogSerializer


class ArtworkLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        data_response = {
            'page_size': self.page_size,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        }
        return Response(data_response)


class ArtworkActivityLogApi(ListAPIView):
    serializer_class = ArtworkLogSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = ArtworkLogPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = (
        'artwork__title',
        'artwork__inventory_code',
    )
    ordering_fields = (
        'created_at',
    )

    def get_queryset(self):
        user = self.request.user
        queryset = ArtworkLog.objects.filter(user=user)

        artwork_id = self.request.query_params.get('artwork_id')
        if artwork_id:
            queryset = queryset.filter(artwork_id=artwork_id)

        return queryset.select_related('artwork', 'user')
