from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from artwork.models.artwork import CURRENCY_CHOICES


class CurrencyArtworkApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        list_currency = [{'key': key, 'value': value} for key, value in CURRENCY_CHOICES]

        return Response(list_currency, status=status.HTTP_200_OK)
