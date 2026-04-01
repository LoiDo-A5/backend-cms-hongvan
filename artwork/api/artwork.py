import django_filters
import uuid
from datetime import timedelta

import jwt
from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from artwork.models import ArtWork, ArtworkArtist
from artwork.models.artwork_certificate import ArtworkCertificate
from artwork.models.collector_ownership_transfer import CollectorOwnershipTransfer
from artwork.models.artwork_edition import ArtworkEdition
from artwork.serializers.artwork import ArtWorkCreateSerializer
from artwork.serializers.artwork import ArtWorkUpdateFullFieldSerializer
from artwork.serializers.artwork import ArtWorkUpdateLessFieldSerializer
from artwork.serializers.artwork import ArtworkEditionNumberSerializer
from artwork.serializers.artwork import ArtworkEditionSerializer
from artwork.serializers.artwork import ArtworkInStockUpdateSerializer
from artwork.serializers.artwork import ArtworkSerializer
from artwork.serializers.artwork import ArtworkViewInfoSerializer
from artwork.serializers.artwork import CertificateSerializer
from artwork.serializers.artwork import CollectorArtWorkUpdateSerializerData
from artwork.serializers.artwork import CollectorRequestCertificateSerializer
from artwork.serializers.artwork import CreateCertificateSerializer
from artwork.utils.artwork import (
    get_filtered_artworks,
    process_artists_data,
)
from artwork.utils.mixin.share_link import ShareLinkArtworkMixin
from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User
from core.accounts.models.user import USER_ROLE


class ArtworkPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        data_response = {
            'page_size': self.page_size,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        }
        return Response(data_response)


class ArtWorkFilter(filters.FilterSet):
    price = django_filters.CharFilter(method='filter_by_price')
    year = django_filters.CharFilter(method='filter_by_year')
    artist = django_filters.CharFilter(method='filter_by_artist')

    class Meta:
        model = ArtWork
        fields = {
            'category': ['in'],
            'style': ['in'],
            'subject': ['in'],
            'medium': ['in'],
            'orientation': ['in'],
            'status': ['in'],
            'location': ['in'],
            'is_public': ['exact'],
        }

    def filter_by_price(self, queryset, name, value):
        return self.filter_by_numeric_range(queryset, name, value, 'price')

    def filter_by_year(self, queryset, name, value):
        return self.filter_by_numeric_range(queryset, name, value, 'year_created')

    def filter_by_artist(self, queryset, name, value):
        query_value = value.split(',')
        return queryset.filter(
            Q(artist_artwork__artist_name__in=query_value) | Q(artist__name__in=query_value),
        )

    def filter_by_numeric_range(self, queryset, name, value, field_name):
        range_values = value.split(',')

        if len(range_values) == 1:
            min_value = float(range_values[0])
            filter_kwargs = {f'{field_name}__gte': min_value}
            return queryset.filter(**filter_kwargs)

        min_value, max_value = map(float, range_values)
        filter_kwargs = {
            f'{field_name}__gte': min_value,
            f'{field_name}__lte': max_value,
        }
        return queryset.filter(**filter_kwargs)


class CustomOrderingFilter(OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)

        if not ordering:
            return []

        new_ordering = []

        for field in ordering:
            if field.startswith('-'):
                field_name = field.lstrip('-')
                ordering_expression = F(field_name).desc(nulls_last=True)
            else:
                ordering_expression = F(field).asc(nulls_last=True)

            new_ordering.append(ordering_expression)

        return new_ordering


class ArtworkViewSet(ShareLinkArtworkMixin, ModelViewSet):
    queryset = ArtWork.objects.all().order_by('-id')
    serializer_class = ArtworkSerializer
    pagination_class = ArtworkPagination
    lookup_url_kwarg = 'uuid'
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, CustomOrderingFilter)
    filterset_class = ArtWorkFilter
    search_fields = (
        'title', 'id', 'inventory_code', 'medium__name', 'medium__name_vi',
        'subjects__name', 'subjects__name_vi', 'year_created',
        'artist__name', 'artist_name', 'artist_artwork__artist_name',
    )
    ordering_fields = ('price', 'year_created')
    certificate = None

    def get_object(self):
        identifier = self.kwargs.get('uuid', None)

        try:
            identifier_uuid = uuid.UUID(identifier)
        except (TypeError, ValueError):
            raise NotFound()

        try:
            self.certificate = get_object_or_404(ArtworkCertificate, code=identifier_uuid)
            return self.certificate.artwork_edition.artwork
        except Http404:
            pass

        try:
            return get_object_or_404(ArtWork.all_objects, uuid=identifier_uuid)
        except Http404:
            raise NotFound()

    def get_update_artwork_serializer(self):
        artwork = self.get_object()

        if artwork.has_certificate():
            return ArtWorkUpdateLessFieldSerializer

        return ArtWorkUpdateFullFieldSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user_uuid = self.request.query_params.get('user_uuid', None)

        user = self.request.user
        owner_uuid = getattr(user, 'uuid', '')
        is_owner = str(owner_uuid) == user_uuid

        if not is_owner:
            queryset = queryset.filter(owner__uuid=user_uuid, is_public=True)

        return queryset.filter(owner__uuid=user_uuid)

    def get_serializer_class(self):
        artwork_view_info_actions = [
            'artwork_view_info',
            'list_artwork_by_artist',
        ]

        if self.action in artwork_view_info_actions:
            return ArtworkViewInfoSerializer
        if self.action == 'create':
            return ArtWorkCreateSerializer
        if self.action == 'partial_update':
            return self.get_update_artwork_serializer()
        if self.action == 'update_artwork_in_stock':
            return ArtworkInStockUpdateSerializer
        if self.action == 'create_certificate':
            return CreateCertificateSerializer
        if self.action == 'request_certificate':
            return CollectorRequestCertificateSerializer
        return super().get_serializer_class()

    def perform_destroy(self, instance):
        if not instance.has_owner(self.request.user):
            raise PermissionDenied('You do not have permission to delete this artwork.')
        try:
            instance._current_user = self.request.user
        except Exception:
            pass
        instance.delete()

    def perform_update(self, serializer):
        artwork = self.get_object()
        is_owner = artwork.has_owner(self.request.user)
        if not is_owner:
            raise PermissionDenied('You do not have permission to edit this artwork.')

        serializer.save(_current_user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = self.request.user
        is_owner = instance.has_owner(user)

        if not instance.is_public and not is_owner:
            raise PermissionDenied('You do not have permission to access this artwork.')

        if self.certificate:
            instance.certificate = self.certificate

        serializer = self.get_serializer(instance)

        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def create_certificate(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        certificate = serializer.process()
        response_serializer = CertificateSerializer(certificate)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def editions_can_request_certificate(self, *args, **kwargs):
        artwork = self.get_object()

        ids = ArtworkEdition.objects.filter(linked_edition__artwork_id=artwork.id,
                                            certificate__isnull=False).values_list('linked_edition_id', flat=True)

        editions = artwork.editions.filter(certificate__isnull=True).exclude(id__in=ids).order_by('edition_number')

        serializer = ArtworkEditionNumberSerializer(editions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def request_certificate(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        artwork = self.get_object()
        artwork_serializer = CollectorArtWorkUpdateSerializerData(instance=artwork, data=self.request.data['artwork'],
                                                                  partial=True, context=self.get_serializer_context())
        artwork_serializer.is_valid(raise_exception=True)

        edition = get_object_or_404(ArtworkEdition, pk=self.request.data['edition']['id'])

        edition_serialize = ArtworkEditionSerializer(instance=edition, data=self.request.data['edition'], partial=True)
        edition_serialize.is_valid(raise_exception=True)

        artwork_serializer.save()
        edition_serialize.save()

        certificate_request = serializer.process(edition)
        response_data = serializer.data
        response_data['id'] = certificate_request.id

        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def list_eligible_artwork(self, *args, **kwargs):
        artworks = ArtWork.objects.filter(is_public=True).order_by('-id')
        artworks = self.filter_queryset(artworks)
        paginator = ArtworkPagination()
        paginator.page_size = 24
        page = paginator.paginate_queryset(artworks, self.request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def list_gallery_artwork(self, *args, **kwargs):
        share_link_id = self.request.query_params.get('share_link_id', None)
        if share_link_id:
            artworks = self.get_shared_artworks(
                request=self.request,
                share_link_id=share_link_id,
            )
        else:
            user_uuid = self.request.query_params.get('user_uuid')
            user = self.request.user
            is_owner = user.uuid == user_uuid

            if not is_owner:
                raise PermissionDenied('You do not have permission to access this artwork.')

            artworks = ArtWork.objects.filter(owner_id=user.id)

        artworks = self.filter_queryset(artworks)
        paginator = ArtworkPagination()
        paginator.page_size = 24
        page = paginator.paginate_queryset(artworks.order_by('-id'), self.request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def list_artwork_same_collection(self, *args, **kwargs):
        user_id = self.request.query_params.get('user_id', None)
        year_created = self.request.query_params.get('year_created', None)
        artwork_id = self.request.query_params.get('artwork_id', None)
        owner_id = self.request.query_params.get('owner_id', None)

        if not owner_id:
            return Response([], status=status.HTTP_200_OK)
        owner = User.objects.get(id=owner_id)

        filter_params = {
            'is_public': True,
        }

        if owner.role == USER_ROLE.ARTIST:
            filter_params['owner_id'] = owner_id
            if year_created is not None:
                filter_params['year_created'] = int(year_created)
            artworks = ArtWork.objects.filter(**filter_params).exclude(id=artwork_id).order_by('-year_created',
                                                                                               '-id')[:4]

        elif owner.role == USER_ROLE.COLLECTOR:
            filter_params['artist_id'] = user_id
            if year_created is not None:
                filter_params['year_created'] = int(year_created)
            artworks = ArtWork.objects.filter(**filter_params).order_by('-year_created', '-id')[:4]

        else:
            return Response([], status=status.HTTP_200_OK)

        serializer = self.get_serializer(artworks, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def list_artworks_for_selection(self, *args, **kwargs):
        qs = self.get_queryset().order_by('-id')
        artworks = self.filter_queryset(qs)
        paginator = ArtworkPagination()
        paginator.page_size = 18
        page = paginator.paginate_queryset(artworks, self.request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST'])
    def like(self, request, *args, **kwargs):
        request.user.like_artworks.get_or_create(artwork=self.get_object())
        return Response({'message': 'Like Success'}, status.HTTP_200_OK)

    @action(detail=True, methods=['POST'])
    def unlike(self, request, *args, **kwargs):
        request.user.like_artworks.filter(artwork=self.get_object()).delete()
        return Response({'message': 'Unlike Success'}, status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def list_artwork_excluding_sold_donated_gifted(self, *args, **kwargs):
        user_uuid = self.request.query_params.get('user_uuid', None)
        base_queryset = ArtWork.objects.filter(owner__uuid=user_uuid).exclude(
            status__in=['sold', 'donated_gifted']).order_by('-id')
        queryset = self.filter_queryset(base_queryset)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def list_collector_sold_donated(self, request, *args, **kwargs):
        user = request.user
        if not getattr(user, 'is_authenticated', False) or user.role != USER_ROLE.COLLECTOR:
            raise PermissionDenied()

        base_artworks = ArtWork.objects.filter(
            owner=user,
            status__in=['sold', 'donated_gifted'],
        ).order_by('-id')
        artworks_qs = self.filter_queryset(base_artworks)

        transfers_qs = CollectorOwnershipTransfer.objects.filter(transferrer=user)
        search = request.query_params.get('search', '').strip()
        if search:
            transfers_qs = transfers_qs.filter(
                Q(snapshot__title__icontains=search) | Q(snapshot__inventory_code__icontains=search),
            )

        artwork_meta = list(artworks_qs.values('id', 'updated_at'))
        transfer_meta = list(transfers_qs.values('id', 'transferred_at'))

        combined = []
        for row in artwork_meta:
            combined.append((row['updated_at'], 'artwork', row['id']))
        for row in transfer_meta:
            combined.append((row['transferred_at'], 'transfer', row['id']))

        combined.sort(key=lambda x: x[0], reverse=True)

        page_size = ArtworkPagination.page_size
        paginator = Paginator(combined, page_size)
        page_num = int(request.query_params.get('page', 1) or 1)
        try:
            page_obj = paginator.page(page_num)
        except EmptyPage:
            page_obj = paginator.page(1)

        serializer_context = {'request': request}
        results = []
        for _sort_date, kind, pk in page_obj.object_list:
            if kind == 'artwork':
                artwork = ArtWork.objects.get(pk=pk)
                row = ArtworkSerializer(artwork, context=serializer_context).data
                row['is_ownership_transfer_record'] = False
                row['transferee'] = None
                results.append(row)
            else:
                record = CollectorOwnershipTransfer.objects.select_related('transferee').get(pk=pk)
                row = dict(record.snapshot)
                row['is_ownership_transfer_record'] = True
                row['ownership_transfer_id'] = record.id
                row['list_row_key'] = f'transfer-{record.id}'
                row['transferee'] = UserSerializer(record.transferee, context=serializer_context).data
                results.append(row)

        return Response({
            'count': paginator.count,
            'page_size': page_size,
            'next': None,
            'previous': None,
            'results': results,
        })

    @action(detail=True, methods=['get'])
    def artwork_view_info(self, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def list_artist_name_for_collector(self, request, *args, **kwargs):
        share_link_id = self.request.query_params.get('share_link_id', None)

        if share_link_id:
            base_artworks = self.get_shared_artworks(
                request=self.request,
                share_link_id=share_link_id,
            )
            owner = base_artworks.values('owner_id').first()
            owner_id = owner.get('owner_id') if owner else None
            user = User.objects.filter(id=owner_id).first()
        else:
            user_uuid = self.request.query_params.get('user_uuid', None)

            if not user_uuid:
                raise PermissionDenied('You do not have permission to access this artist list.')

            user = get_object_or_404(User, uuid=user_uuid)
            user_request = self.request.user
            is_owner = getattr(user_request, 'is_authenticated', False) and str(user_request.uuid) == user_uuid

            if not is_owner:
                raise PermissionDenied('You do not have permission to access this artist list.')

            base_artworks = ArtWork.objects.filter(owner=user)

        official_artists = base_artworks.filter(
            artist__isnull=False,
        ).values(
            'artist_id', 'artist__uuid', 'artist__name', 'artist__year_of_birth',
        ).annotate(
            artwork_count=Count('id'),
        ).exclude(artwork_count=0)

        manual_artists_queryset = ArtworkArtist.objects.filter(create_user=user)
        if share_link_id:
            artwork_ids = list(base_artworks.values_list('id', flat=True))
            manual_artists_queryset = manual_artists_queryset.filter(artworks__id__in=artwork_ids)

        manual_artists = manual_artists_queryset.values(
            'artist_name', 'year_of_birth', 'id',
        ).annotate(
            artwork_count=Count(
                'artworks__id',
                filter=Q(artworks__owner=user),
            ),
        ).exclude(artwork_count=0)

        search_term = self.request.query_params.get('search', '').strip()
        ordering = self.request.query_params.get('ordering', '')
        artists = process_artists_data(official_artists, manual_artists, search_term, ordering)

        paginator = ArtworkPagination()
        paginator.page_size = 24
        page = self.request.query_params.get('page', 1)
        paginator.page = page

        paginated_artists = paginator.paginate_queryset(artists, request)
        return paginator.get_paginated_response(paginated_artists)

    @action(detail=False, methods=['get'])
    def list_artwork_by_artist(self, request, *args, **kwargs):
        owner_uuid = self.request.query_params.get('owner_uuid')
        artist_uuid = self.request.query_params.get('artist_uuid')
        artist_artwork_id = self.request.query_params.get('artist_artwork_id')

        owner = get_object_or_404(User, uuid=owner_uuid)
        is_owner = self.request.user.id == owner.id

        artworks = get_filtered_artworks(owner, artist_uuid, artist_artwork_id, is_owner)
        serializer = self.get_serializer(artworks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def create_single_artist_token(self, request, *args, **kwargs):
        user_uuid = str(self.request.user.uuid)
        expires_at = timezone.now() + timedelta(days=365 * 10)  # 10 years

        payload = {
            'user_uuid': user_uuid,
            'expires_at': int(expires_at.timestamp()),
            'scope': 'single_artist',
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return Response(token, status=201)

    @action(detail=False, methods=['get'])
    def create_share_link(self, request, *args, **kwargs):
        user_uuid = str(self.request.user.uuid)
        expires_at = timezone.now() + timedelta(minutes=30)

        payload = {
            'user_uuid': user_uuid,
            'expires_at': int(expires_at.timestamp()),
            'scope': 'create_share_link',
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return Response(token, status=201)

    @action(detail=False, methods=['get'])
    def list_special_artwork(self, *args, **kwargs):
        user_uuid = self.request.query_params.get('user_uuid')
        artworks = ArtWork.objects.filter(is_public=True, owner__uuid=user_uuid).order_by('-id')[:4]
        serializer = self.get_serializer(artworks, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def list_artwork_in_stock(self, *args, **kwargs):
        user_uuid = self.request.query_params.get('user_uuid')
        artworks = ArtWork.all_objects.filter(owner__uuid=user_uuid, status='in_stock', active=True)
        page = self.paginate_queryset(artworks)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_artwork_in_stock(self, request, *args, **kwargs):
        artwork = self.get_object()

        serializer = self.get_serializer(artwork, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(_current_user=request.user)

        return Response(serializer.data, status=status.HTTP_200_OK)
