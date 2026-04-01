from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User
from core.accounts.models.user import USER_ROLE


class UserGladiusIdFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'role': ['in'],
        }


class SearchUserGladiusIDApiView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = UserGladiusIdFilter

    def get_queryset(self):
        query_params = self.request.query_params

        search_raw = query_params.get('search')
        if search_raw is None:
            return User.objects.none()

        search = search_raw.strip()
        if not search:
            return User.objects.none()

        return User.objects.filter(uuid__iexact=search).order_by('id')

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        raw_role_in = self.request.query_params.get('role__in')
        if raw_role_in is None or (isinstance(raw_role_in, str) and raw_role_in.strip() == ''):
            queryset = queryset.filter(role=USER_ROLE.ARTIST)
        return queryset
