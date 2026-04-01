import django_filters
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter


from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User


class UserFilter(filters.FilterSet):
    exclude__in = django_filters.CharFilter(method='filter_exclude_user')
    include_me = django_filters.CharFilter(method='filter_include_me')

    class Meta:
        model = User
        fields = {
            'role': ['in'],
        }

    def filter_exclude_user(self, queryset, name, value):
        exclude_user_ids = value.split(',')
        return queryset.exclude(id__in=exclude_user_ids)

    def filter_include_me(self, queryset, name, value):
        search_params = self.request.query_params.get('search', None)
        if not search_params:
            return queryset

        query_ids = queryset.values_list('id', flat=True)
        ids = [self.request.user.id] + list(query_ids)
        return User.objects.filter(id__in=ids).order_by('id')


class SearchUserApiView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        query_params = self.request.query_params

        search_params = query_params.get('search', None)
        if not search_params:
            return User.objects.none()

        queryset = User.objects.all().order_by('id')
        return queryset

    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    filterset_class = UserFilter
    search_fields = ('legal_name', 'profile__nick_name', 'name', 'uuid')
