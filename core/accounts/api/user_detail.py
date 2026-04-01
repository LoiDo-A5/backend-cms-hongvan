from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.generics import get_object_or_404
from rest_framework import status

from ..models import User


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['avatar', 'name', 'email', 'phone_number']


class UserDetailApi(GenericAPIView):
    def post(self, request):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        if not user.is_active:
            return Response(
                {'message': 'Your account has been deactivated.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserDetailSerializer(instance=user)
        return Response(serializer.data)
