from rest_framework.views import APIView
from rest_framework.response import Response

from artwork.models import ArtWork


class FilterArtistByUserApi(APIView):
    def get(self, request, *args, **kwargs):
        user_artworks = ArtWork.objects.filter(owner=request.user)

        platform_artists = user_artworks.filter(artist__isnull=False).values_list('artist__name', flat=True)
        manual_artists = user_artworks.filter(
            artist_artwork__isnull=False,
        ).values_list('artist_artwork__artist_name', flat=True)

        artists = set(platform_artists) | set(manual_artists)

        return Response(sorted(list(artists)))
