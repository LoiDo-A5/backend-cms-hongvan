from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from artwork.models.artwork import STATUS_CHOICES


EXCLUDE_STATUS = ['under_maintenance', 'lost', 'not_for_sale', 'in_stock']


class StatusCanRequestCertificateApi(APIView):

    def get(self, request, *args, **kwargs):
        list_status = [
            {'key': key, 'value': value}
            for key, value in STATUS_CHOICES
            if key and key not in EXCLUDE_STATUS]

        return Response(list_status, status=status.HTTP_200_OK)
