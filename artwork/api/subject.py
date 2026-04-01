from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView

from artwork.api.style import FilterUserExtendAttribute
from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import SubjectArtwork
from artwork.serializers.subject import SubjectArtworkSerializer


class SubjectArtworkFilter(filters.FilterSet):
    category = filters.ChoiceFilter(choices=CATEGORY_CHOICES)

    class Meta:
        model = SubjectArtwork
        fields = ('category',)


class SubjectArtworkApi(FilterUserExtendAttribute, ListAPIView):
    queryset = SubjectArtwork.objects.all().order_by('pk')
    serializer_class = SubjectArtworkSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = SubjectArtworkFilter
