from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter

from artwork.models.artwork import ArtWork
from artwork.serializers.artwork import ArtworkSerializer


class SearchAutocomplete(ListAPIView):
    queryset = ArtWork.objects.all().order_by('-id')
    serializer_class = ArtworkSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend, SearchFilter)
    search_fields = ('title',)
    filterset_fields = ('owner',)

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)

        if not search:
            return ArtWork.objects.none()

        return queryset
