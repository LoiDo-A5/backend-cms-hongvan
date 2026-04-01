from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import serializers

from rest_framework.viewsets import ModelViewSet

from django_filters import rest_framework as filters

from core.accounts.models import UserCollection


class CollectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCollection
        fields = ('name', 'is_public')

    def create(self, validated_data):
        user = self.context['request'].user
        exhibition = UserCollection.objects.create(user=user, **validated_data)
        return exhibition


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCollection
        fields = '__all__'


class UserCollectionFilter(filters.FilterSet):
    class Meta:
        model = UserCollection
        fields = {'is_public': ['exact']}


class CollectionViewSet(ModelViewSet):
    queryset = UserCollection.objects.all()
    serializer_class = CollectionSerializer
    lookup_url_kwarg = 'pk'
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserCollectionFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        user_uuid = getattr(self.request.user, 'uuid', None)

        if self.action == 'list':
            user_uuid = self.request.query_params.get('user_uuid', user_uuid)

        queryset = queryset.filter(user__uuid=user_uuid)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return CollectionCreateSerializer
        return super().get_serializer_class()
