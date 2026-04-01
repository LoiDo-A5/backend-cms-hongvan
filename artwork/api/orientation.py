from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView

from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import OrientationArtwork
from artwork.serializers.orientation import OrientationArtworkSerializer


class OrientationArtworkFilter(filters.FilterSet):
    category = filters.ChoiceFilter(choices=CATEGORY_CHOICES)

    class Meta:
        model = OrientationArtwork
        fields = ('category',)


class OrientationArtworkApi(ListAPIView):
    queryset = OrientationArtwork.objects.all().order_by('pk')
    serializer_class = OrientationArtworkSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = OrientationArtworkFilter
