from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from artwork.models import Exhibition
from core.accounts.models import User


class ExhibitionCountApi(APIView):

    def get(self, request):
        owner_uuid = request.query_params.get('owner_uuid')
        owner = get_object_or_404(User, uuid=owner_uuid)
        user_request = self.request.user
        is_owner = user_request.id == owner.id

        if not is_owner:
            exhibition_count = Exhibition.objects.filter(owner_id=owner.id, is_public=True).count()
        else:
            exhibition_count = Exhibition.objects.filter(owner_id=owner.id).count()

        return Response(exhibition_count)
