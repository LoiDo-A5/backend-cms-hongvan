from rest_framework import serializers
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from core.accounts.models import User


class ChangeLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'language',
        )


class ChangeLanguageApi(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ChangeLanguageSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
