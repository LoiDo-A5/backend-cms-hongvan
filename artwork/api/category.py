from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from artwork.utils.const import CATEGORY_CHOICES


class CategoryArtworkApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        list_status = [{'key': key, 'value': value} for key, value in CATEGORY_CHOICES if key]

        return Response(list_status, status=status.HTTP_200_OK)
