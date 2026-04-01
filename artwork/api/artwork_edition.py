from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from artwork.models import ArtWork, ArtworkEdition
from artwork.serializers.artwork_edition import ArtworkEditionSerializer


class ArtworkEditionPagination(PageNumberPagination):
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


class ArtworkEditionApi(ListAPIView):
    queryset = ArtWork.objects.all()
    serializer_class = ArtworkEditionSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = ArtworkEditionPagination
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
    )
    search_fields = ('title',)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user).prefetch_related(
            Prefetch(
                'editions',
                queryset=ArtworkEdition.objects.select_related('transferee', 'location'),
            ),
        ).order_by('-id')
