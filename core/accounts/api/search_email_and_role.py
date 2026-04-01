from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .user_api import UserSerializer
from ..models import User


class SearchUserByEmailAndRoleApi(APIView):
    def get(self, request, *args, **kwargs):
        email = request.query_params.get('email')
        roles = request.query_params.get('role')
        role_request = request.query_params.get('role_request')
        roles = roles.split(',')

        if role_request != '1' and request.user.is_authenticated and email == request.user.email:
            return Response({
                'message': 'You cannot search for yourself.',
            }, status=status.HTTP_404_NOT_FOUND)

        if role_request == '1' and request.user.is_authenticated and email == request.user.email:
            serializer = UserSerializer(request.user)
            return Response([serializer.data], status=status.HTTP_200_OK)

        if email:
            users_with_email = User.objects.filter(email=email)

            users_with_email_and_roles = users_with_email.filter(role__in=roles)
            if users_with_email.exists() and not users_with_email_and_roles.exists():
                return Response({
                    'message': 'Email exists but the user does not have the requested roles. Please search again.',
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = UserSerializer(users_with_email_and_roles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
