from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView

from artwork.api.style import FilterUserExtendAttribute
from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import MediumArtwork
from artwork.serializers.artwork import MediumSerializer


class MediumArtworkFilter(filters.FilterSet):
    category = filters.ChoiceFilter(choices=CATEGORY_CHOICES)

    class Meta:
        model = MediumArtwork
        fields = ('category',)


class MediumArtworkApi(FilterUserExtendAttribute, ListAPIView):
    queryset = MediumArtwork.objects.all().order_by('pk')
    serializer_class = MediumSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MediumArtworkFilter
