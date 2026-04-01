from rest_framework.permissions import IsAuthenticatedOrReadOnly

from rest_framework.viewsets import ModelViewSet

from core.accounts.models import UserSoloExhibition
from django.db.models import F
from django_filters import rest_framework as filters

from core.accounts.serializers.user_solo_exhibition import SoloExhibitionSerializer
from core.accounts.serializers.user_solo_exhibition import SoloExhibitionCreateSerializer


class UserSoloExhibitionFilter(filters.FilterSet):
    class Meta:
        model = UserSoloExhibition
        fields = {'is_public': ['exact']}


class SoloExhibitionViewSet(ModelViewSet):
    queryset = UserSoloExhibition.objects.all()
    serializer_class = SoloExhibitionSerializer
    lookup_url_kwarg = 'pk'
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserSoloExhibitionFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        user_uuid = getattr(self.request.user, 'uuid', None)

        if self.action == 'list':
            user_uuid = self.request.query_params.get('user_uuid', user_uuid)

        queryset = queryset.filter(user__uuid=user_uuid).order_by(F('year').asc(nulls_last=True))

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return SoloExhibitionCreateSerializer
        return super().get_serializer_class()
