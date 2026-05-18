from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class UserUsablePasswordSerializer(serializers.Serializer):
    has_usable_password = serializers.BooleanField()


class UsablePasswordApi(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserUsablePasswordSerializer

    def get(self, request):
        serializer = self.get_serializer(instance=request.user)
        return Response(serializer.data)
