from django.contrib.auth import authenticate
from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.accounts.api.user_api import UserSerializer


class TokenLoginSerializer(serializers.Serializer):
    password = serializers.CharField()
    username = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField(source='key')
    user = UserSerializer()


class LoginApi(GenericAPIView):
    serializer_class = TokenLoginSerializer
    response_serializer_class = LoginResponseSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self._authenticate_user(request, **serializer.validated_data)

        if not user:
            return Response(
                {
                    'message': gettext('Incorrect username or password'),
                }, status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.has_activated:
            user.has_activated = True
            user.save(update_fields=['has_activated'])

        token, _ = Token.objects.get_or_create(user=user)
        context = self.get_serializer_context()
        response_serializer = self.response_serializer_class(instance=token, context=context)
        return Response(response_serializer.data)

    def _authenticate_user(self, request, **kwargs):
        user = authenticate(request, **kwargs)
        return user
