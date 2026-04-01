from rest_framework.generics import DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from artwork.models import ArtworkEdition
from core.accounts.models.user import USER_ROLE
from django.utils.translation import gettext


class ArtworkEditionDeleteAPIView(DestroyAPIView):
    queryset = ArtworkEdition.objects.all()
    permission_classes = (IsAuthenticated,)
    lookup_field = 'pk'

    def destroy(self, request, *args, **kwargs):
        edition = self.get_object()
        user_role = self.request.user.role

        if not user_role == USER_ROLE.ARTIST:
            raise serializers.ValidationError(gettext('Only users with the artist role can delete this edition.'))
        if edition.has_certificate():
            raise serializers.ValidationError(gettext('Cannot delete edition because'
                                                      ' it has an associated certificate.'))

        return super().destroy(request, *args, **kwargs)
