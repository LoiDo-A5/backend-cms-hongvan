from rest_framework import (
    status,
)
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from core.accounts.models import UserSignalId


class DeleteSignalId(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        signal_id = request.data.get('signal_id')

        signal = get_object_or_404(UserSignalId, user=user, signal_id=signal_id)
        signal.delete()
        return Response({'detail': 'Signal ID deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
