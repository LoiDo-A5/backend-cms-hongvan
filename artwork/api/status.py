from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from artwork.models.artwork import STATUS_CHOICES


class StatusArtworkApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        list_status = [
            {'key': key, 'value': value}
            for key, value in STATUS_CHOICES
            if key and key != 'in_stock'
        ]

        return Response(list_status, status=status.HTTP_200_OK)
