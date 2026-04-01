from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework import serializers
from django.utils.translation import gettext

from core.accounts.models import UserLocation


class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = ('id', 'user', 'location')

    def validate_location(self, value):
        user = self.context['request'].user
        existing_location = UserLocation.objects.filter(user=user, location=value).exists()
        if existing_location:
            raise serializers.ValidationError(gettext('Location name already exists in your list.'))
        return value


class LocationApi(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = UserLocation.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = UserLocationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)
