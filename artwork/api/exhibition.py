from artwork.api.artwork import ArtworkPagination
from artwork.models import Exhibition, ArtworkArtist
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.filters import SearchFilter
from django_filters import rest_framework as filters
from django.db.models import Count, Q

from artwork.serializers.exhibition import ExhibitionSerializer, ExhibitionUpdateSerializer
from artwork.serializers.exhibition import ExhibitionCreateSerializer
from artwork.serializers.exhibition import ExhibitionSaveAsDraftSerializer
from artwork.utils.artwork import process_artists_data
from artwork.models import ArtWork


class ExhibitionPagination(PageNumberPagination):
    page_size = 12

    def get_paginated_response(self, data):
        data_response = {
            'page_size': self.page_size,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        }
        return Response(data_response)


class ExhibitionViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        GenericViewSet):
    queryset = Exhibition.objects.all().order_by('-id')
    serializer_class = ExhibitionSerializer
    lookup_url_kwarg = 'pk'
    pagination_class = ExhibitionPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    search_fields = ('title',)
    filterset_fields = ('is_public',)

    def get_object(self):
        pk = self.kwargs.get('pk', None)
        return get_object_or_404(Exhibition, pk=pk)

    def get_queryset(self):
        queryset = super().get_queryset()
        user_uuid = self.request.query_params.get('user_uuid', None)

        user = self.request.user
        uuid = getattr(user, 'uuid', '')
        is_owner = str(uuid) == user_uuid

        if not is_owner:
            queryset = queryset.filter(owner__uuid=user_uuid, is_public=True, is_draft=False)

        return queryset.filter(owner__uuid=user_uuid)

    def get_serializer_class(self):
        if self.action == 'create':
            return ExhibitionCreateSerializer
        if self.action == 'partial_update':
            return ExhibitionUpdateSerializer
        if self.action == 'save_as_draft':
            return ExhibitionSaveAsDraftSerializer
        return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        exhibition = self.get_object()
        user = self.request.user
        is_owner = exhibition.has_owner(user)
        if not exhibition.is_public and not is_owner:
            raise PermissionDenied('You do not have permission to access this exhibition.')

        serializer = self.get_serializer(exhibition)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        if not instance.has_owner(self.request.user):
            raise PermissionDenied('You do not have permission to delete this exhibition.')
        instance.delete()

    def perform_update(self, serializer):
        exhibition = self.get_object()
        is_owner = exhibition.has_owner(self.request.user)
        if not is_owner:
            raise PermissionDenied('You do not have permission to edit this exhibition.')
        super().perform_update(serializer)

    @action(detail=False, methods=['post'])
    def save_as_draft(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.validated_data['is_draft'] = True
        serializer.validated_data['owner'] = user
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def list_artist_name(self, request, *args, **kwargs):
        exhibition = self.get_object()
        artworks_in_exhibition = exhibition.groups.values_list('artworks', flat=True)

        official_artists = ArtWork.objects.filter(
            id__in=artworks_in_exhibition,
            artist__isnull=False,
        ).values(
            'artist_id', 'artist__uuid', 'artist__name', 'artist__year_of_birth',
        ).annotate(
            artwork_count=Count('id'),
        ).exclude(artwork_count=0)

        manual_artists = (
            ArtworkArtist.objects.filter(artworks__in=artworks_in_exhibition)
            .values(
                'artist_name',
                'year_of_birth',
                'id',
            )
            .annotate(
                artwork_count=Count('artworks__id', filter=Q(artworks__in=artworks_in_exhibition)),
            )
            .exclude(artwork_count=0)
        )

        search_term = self.request.query_params.get('search', '').strip()
        ordering = self.request.query_params.get('ordering', '')

        artists = process_artists_data(official_artists, manual_artists, search_term, ordering)

        paginator = ArtworkPagination()
        paginator.page_size = 24
        page = self.request.query_params.get('page', 1)
        paginator.page = page

        paginated_artists = paginator.paginate_queryset(artists, request)
        return paginator.get_paginated_response(paginated_artists)
