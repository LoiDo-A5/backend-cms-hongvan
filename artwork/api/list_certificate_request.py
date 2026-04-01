from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from artwork.models import CertificateRequest
from artwork.serializers.certificate_request import BaseCertificateRequestSerializer
from core.accounts.models.user import USER_ROLE


class RequestCertificatePagination(PageNumberPagination):
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


# TODO: remove ListCertificateRequestApi, duplicate with CertificateRequestViewSet
class ListCertificateRequestApi(ListAPIView):
    queryset = CertificateRequest.objects.all()
    serializer_class = BaseCertificateRequestSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = RequestCertificatePagination
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
    )
    search_fields = ('artwork_edition__artwork__title', 'status')

    def get_queryset(self):
        queryset = super().get_queryset()
        user_role = self.request.user.role
        if user_role == USER_ROLE.COLLECTOR:
            return queryset.filter(request_by=self.request.user).order_by('-id')
        elif user_role == USER_ROLE.ARTIST:
            return queryset.filter(request_to=self.request.user).order_by('-id')
        else:
            return queryset.none()
