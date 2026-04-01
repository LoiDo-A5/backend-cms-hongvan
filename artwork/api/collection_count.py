from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from artwork.models import Collection
from core.accounts.models import User
from core.accounts.models.user import USER_ROLE


class CollectionCountApi(APIView):

    def get(self, request):
        owner_uuid = request.query_params.get('owner_uuid')
        owner = get_object_or_404(User, uuid=owner_uuid)
        user_request = self.request.user
        is_owner = user_request.id == owner.id
        collection_count = 0

        if owner.role == USER_ROLE.ARTIST:
            collection_count = Collection.objects.filter(owner_id=owner.id).count()
            if not is_owner:
                collection_count = Collection.objects.filter(owner_id=owner.id, is_public=True).count()

        elif owner.role == USER_ROLE.COLLECTOR:
            if is_owner:
                collection_count = Collection.objects.filter(owner_id=owner.id).count()
            else:
                return Response(collection_count)

        return Response(collection_count)
