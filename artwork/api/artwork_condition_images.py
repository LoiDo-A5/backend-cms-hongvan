from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView

from artwork.models.artwork import ArtWork
from artwork.models.condition_image_batch import ConditionImage
from artwork.serializers.condition_image import ConditionImageSerializer


class ArtworkConditionImagesApi(ListAPIView):
    serializer_class = ConditionImageSerializer

    def get_queryset(self):
        artwork_id = self.kwargs.get('artwork_id')
        get_object_or_404(ArtWork.all_objects, id=artwork_id)

        return ConditionImage.objects.filter(
            batch__artwork_id=artwork_id,
        ).select_related(
            'batch',
            'batch__owner',
        ).order_by('batch__created_at')
