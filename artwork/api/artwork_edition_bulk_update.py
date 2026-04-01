from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from artwork.models import ArtworkEdition, ArtWork
from artwork.serializers.artwork import ArtworkEditionSerializer
from rest_framework import status


class ArtworkEditionBulkUpdateApi(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        data = request.data
        artwork_statuses = set()
        artwork_ids_updated = set()

        for item in data:
            edition_instance = get_object_or_404(ArtworkEdition, id=item.get('id'))
            serializer = ArtworkEditionSerializer(edition_instance, data=item, partial=True)
            if serializer.is_valid():
                serializer.save()
                artwork_ids_updated.add(edition_instance.artwork.id)
                artwork_statuses.add((edition_instance.artwork.id, item.get('status')))
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        for artwork_id in artwork_ids_updated:
            edition_statuses = [edition_status for art_id, edition_status in artwork_statuses if art_id == artwork_id]
            artwork = ArtWork.objects.get(id=artwork_id)

            editions = artwork.editions.all()
            if editions.count() == 1:
                artwork.location = editions.first().location

            if any(edition_status in ['available', 'consignment'] for edition_status in edition_statuses):
                artwork.status = 'available'
            elif any(edition_status == 'sold' for edition_status in edition_statuses) and not any(
                    edition_status in ['available', 'consignment'] for edition_status in edition_statuses):
                artwork.status = 'sold'
            elif not any(edition_status in ['available', 'consignment', 'sold', 'donated_gifted'] for edition_status in
                         edition_statuses):
                artwork.status = 'not_for_sale'
            else:
                artwork.status = edition_statuses[0] if edition_statuses else artwork.status

            # Set current user for activity log tracking before save
            artwork._current_user = request.user
            artwork.save()

        return Response({'message': 'Artwork Editions updated successfully.'}, status=status.HTTP_200_OK)
