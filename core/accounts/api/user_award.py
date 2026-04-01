from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from core.accounts.models import UserAward
from core.accounts.serializers.user_award import AwardSerializer, AwardListSerializer
from core.accounts.serializers.user_award import AwardPatchSerializer
from core.accounts.serializers.user_award import AwardCreateSerializer
from django.db.models import F
from django_filters import rest_framework as filters


class UserAwardFilter(filters.FilterSet):
    class Meta:
        model = UserAward
        fields = {'is_public': ['exact']}


class AwardViewSet(ModelViewSet):
    queryset = UserAward.objects.all()
    serializer_class = AwardSerializer
    lookup_url_kwarg = 'pk'
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserAwardFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        user_uuid = getattr(self.request.user, 'uuid', None)

        if self.action == 'list':
            user_uuid = self.request.query_params.get('user_uuid', user_uuid)

        queryset = queryset.filter(user__uuid=user_uuid).order_by(F('year').asc(nulls_last=True))

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return AwardListSerializer
        if self.action == 'create':
            return AwardCreateSerializer
        if self.action == 'partial_update':
            return AwardPatchSerializer
        return super().get_serializer_class()
