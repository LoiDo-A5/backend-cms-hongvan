from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from core.accounts.models import User
from core.accounts.serializers.artist import ArtistSerializer


class ArtistPagination(PageNumberPagination):
    page_size = 24

    def get_paginated_response(self, data):
        data_response = {
            'page_size': self.page_size,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        }
        return Response(data_response)


class UserFilter(filters.FilterSet):
    name_startswith = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = User
        fields = ['name_startswith']


class ArtistViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = User.objects.filter(role=1)
    serializer_class = ArtistSerializer
    pagination_class = ArtistPagination
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
    )
    filterset_class = UserFilter
    search_fields = ('name', 'uuid')
