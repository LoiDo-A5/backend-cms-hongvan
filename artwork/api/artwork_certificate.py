from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from artwork.models.artwork_certificate import ArtworkCertificate
from artwork.serializers.artwork_certificate import ArtworkCertificateSerializer
from core.accounts.models.user import USER_ROLE


class ArtworkCertificatePagination(PageNumberPagination):
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


class ArtworkCertificateApi(ListAPIView):
    queryset = ArtworkCertificate.objects.all()
    serializer_class = ArtworkCertificateSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = ArtworkCertificatePagination
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
    )
    search_fields = ('artwork_edition__artwork__title', 'code')

    def get_queryset(self):
        queryset = super().get_queryset()
        user_role = self.request.user.role

        if user_role == USER_ROLE.ARTIST:
            return queryset.filter(issued_by=self.request.user).order_by('-id')

        return queryset.filter(issued_to=self.request.user).order_by('-id')
