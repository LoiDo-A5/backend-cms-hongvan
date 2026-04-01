from rest_framework.permissions import IsAuthenticated

from rest_framework.generics import ListAPIView

from activity_log.models import CertificateLog
from activity_log.serializers.certificate_log import CertificateVerifyLogSerializer
from artwork.utils.const import VERIFY
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class CertificateVerifyLogPagination(PageNumberPagination):
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


class CertificateVerifyLogApi(ListAPIView):
    serializer_class = CertificateVerifyLogSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CertificateVerifyLogPagination

    def get_queryset(self):
        user = self.request.user
        queryset = CertificateLog.objects.filter(user=user, action_type=VERIFY)
        return queryset
