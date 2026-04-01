from django_filters import rest_framework as filters

from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from artwork.models import Collection
from artwork.serializers.collection import CollectionReadSerializer, CollectionReadForEditSerializer
from artwork.serializers.collection import CollectionWriteSerializer
from artwork.api.artwork import CustomOrderingFilter
from artwork.utils.mixin.share_link import ShareLinkCollectionMixin


class CollectionPagination(PageNumberPagination):
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


class CollectionViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.CreateModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        GenericViewSet,
                        ShareLinkCollectionMixin):
    queryset = Collection.objects.all().order_by('-id')
    serializer_class = CollectionReadSerializer
    pagination_class = CollectionPagination
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, CustomOrderingFilter)
    permission_classes = (IsAuthenticatedOrReadOnly,)
    search_fields = ('title',)
    filterset_fields = ('owner', 'is_public')
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action == 'retrieve_collection_for_edit':
            return CollectionReadForEditSerializer
        if self.action in ['create', 'partial_update']:
            return CollectionWriteSerializer
        return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        collection = self.get_object()
        user = self.request.user
        is_owner = collection.has_owner(user)
        if not collection.is_public and not is_owner:
            raise PermissionDenied('You do not have permission to access this collection.')

        serializer = self.get_serializer(collection)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        collection = self.get_object()
        user = self.request.user
        is_owner = collection.has_owner(user)
        if not is_owner:
            raise PermissionDenied('You do not have permission to access this collection.')
        self.perform_destroy(collection)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        collection = self.get_object()
        user = self.request.user
        is_owner = collection.has_owner(user)
        if not is_owner:
            raise PermissionDenied('You do not have permission to update this collection.')
        serializer.save()

    @action(detail=False, methods=['get'])
    def list_owner_collection(self, request, *args, **kwargs):
        user = request.user
        queryset = Collection.objects.filter(owner=user).order_by('-id')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def list_collection_same_artist(self, *args, **kwargs):
        owner_id = self.request.query_params.get('owner_id', None)
        collection_id = self.request.query_params.get('collection_id', None)
        queryset = Collection.objects.filter(
            owner_id=owner_id,
            is_public=True,
            artworks__isnull=False,
            artworks__is_public=True,
        ).exclude(
            id=collection_id,
        ).distinct().order_by('-id')[:4]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def like(self, request, *args, **kwargs):
        request.user.like_collections.get_or_create(collection=self.get_object())
        return Response({'message': 'Like Success'}, status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def unlike(self, request, *args, **kwargs):
        request.user.like_collections.filter(collection=self.get_object()).delete()
        return Response({'message': 'Unlike Success'}, status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def list_gallery_collection(self, request, *args, **kwargs):
        share_link_id = self.request.query_params.get('share_link_id', None)
        if share_link_id:
            collections = self.get_shared_collections(
                request=self.request,
                share_link_id=share_link_id,
            )
        else:
            user_uuid = self.request.query_params.get('user_uuid')
            user = self.request.user
            is_owner = user.uuid == user_uuid

            if not is_owner:
                raise PermissionDenied('You do not have permission to access this collections.')

            collections = Collection.objects.filter(owner_id=user.id)

        collections = self.filter_queryset(collections)
        paginator = CollectionPagination()
        paginator.page_size = 12
        page = paginator.paginate_queryset(collections.order_by('-id'), request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'])
    def retrieve_collection_for_edit(self, request, *args, **kwargs):
        collection = self.get_object()
        user = self.request.user
        is_owner = collection.has_owner(user)

        if not collection.is_public and not is_owner:
            raise PermissionDenied('You do not have permission to access this collection.')

        serializer = self.get_serializer(collection)
        return Response(serializer.data)
