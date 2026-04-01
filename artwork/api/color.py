from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView

from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import ColorArtwork
from artwork.serializers.color import ColorArtworkSerializer


class ColorArtworkFilter(filters.FilterSet):
    category = filters.ChoiceFilter(choices=CATEGORY_CHOICES)

    class Meta:
        model = ColorArtwork
        fields = ('category',)


class ColorArtworkApi(ListAPIView):
    queryset = ColorArtwork.objects.all().order_by('pk')
    serializer_class = ColorArtworkSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ColorArtworkFilter
