from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework.generics import ListAPIView

from core.accounts.models import UserLocation


class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = (
            'id',
            'location',
        )
        ref_name = 'FilterLocationUserLocationSerializer'


class FilterLocationApi(ListAPIView):
    queryset = UserLocation.objects.all().order_by('-id')
    serializer_class = UserLocationSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('user',)
