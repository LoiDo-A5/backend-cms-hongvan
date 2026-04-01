from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.accounts.api.user_api import UserSerializer


class MeRemoveBackgroundApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        user.background = None
        user.save()

        response_serializer = UserSerializer(user)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
