from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView

from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import StyleArtwork
from artwork.serializers.style import StyleArtworkSerializer


class FilterUserExtendAttribute:
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user', None)
        by_artwork_upload = self.request.query_params.get('by_artwork_upload', None)

        if by_artwork_upload:
            return queryset.filter(artwork__owner=self.request.user).distinct()

        if user_id:
            return queryset.filter(user__id=user_id)

        return queryset.filter(user__isnull=True)


class StyleArtworkFilter(filters.FilterSet):
    category = filters.ChoiceFilter(choices=CATEGORY_CHOICES)

    class Meta:
        model = StyleArtwork
        fields = ('category',)


class StyleArtworkApi(FilterUserExtendAttribute, ListAPIView):
    queryset = StyleArtwork.objects.all().order_by('pk')
    serializer_class = StyleArtworkSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = StyleArtworkFilter
