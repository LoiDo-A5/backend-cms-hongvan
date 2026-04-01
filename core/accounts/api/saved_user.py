from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters

from core.accounts.api.user_api import UserSerializer
from core.accounts.models import SavedUser


class SavedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedUser
        fields = ('id', 'user', 'saved_user', 'name_saved_user', 'contact_info_saved_user', 'year_of_birth',
                  'connected_artist')


class ListSavedUserSerializer(serializers.ModelSerializer):
    saved_user = UserSerializer()
    connected_artist = UserSerializer()

    class Meta:
        model = SavedUser
        fields = ('id', 'user', 'saved_user', 'name_saved_user', 'contact_info_saved_user', 'year_of_birth',
                  'connected_artist')


class SavedUserApiView(GenericAPIView):
    serializer_class = SavedUserSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    search_fields = (
        'name_saved_user',
        'connected_artist__name',
    )

    def get_queryset(self):
        queryset = SavedUser.objects.filter(user=self.request.user)
        return queryset.order_by('-created_at')

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        manual_qs = queryset.filter(name_saved_user__isnull=False)[:5]
        connected_qs = queryset.filter(connected_artist__isnull=False)[:5]
        saved_user_qs = queryset.filter(saved_user__isnull=False)[:5]
        combined = list(manual_qs) + list(connected_qs) + list(saved_user_qs)
        serializer = ListSavedUserSerializer(combined, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        saved_user = serializer.validated_data.get('saved_user', None)
        contact_info_saved_user = serializer.validated_data.get('contact_info_saved_user', None)
        name_saved_user = serializer.validated_data.get('name_saved_user', None)
        connected_artist = serializer.validated_data.get('connected_artist', None)

        existing_saved_user = SavedUser.objects.filter(
            user=user, saved_user=saved_user, contact_info_saved_user=contact_info_saved_user,
            name_saved_user=name_saved_user, connected_artist=connected_artist,
        ).first()

        if existing_saved_user:
            instance = existing_saved_user
        else:
            instance = serializer.save(user=user)

        saved_users = SavedUser.objects.filter(user=user).order_by('-created_at').values_list('id', flat=True)
        if saved_users.count() > 10:
            SavedUser.objects.filter(id__in=saved_users[200:]).delete()

        response_serializer = self.get_serializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
