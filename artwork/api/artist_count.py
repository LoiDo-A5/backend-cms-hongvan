from rest_framework.views import APIView
from rest_framework.response import Response

from artwork.models import ArtWork, ArtworkArtist


class ArtistCountApi(APIView):

    def get(self, request):
        user = self.request.user

        official_artist_count = (
            ArtWork.objects.filter(owner=user, artist__isnull=False).values('artist').distinct().count()
        )
        manual_artist_count = ArtworkArtist.objects.filter(create_user=user).count()

        total = official_artist_count + manual_artist_count

        return Response(total)
