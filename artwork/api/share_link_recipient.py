from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from artwork.models.share_link import ShareLink
from core.accounts.models import User
from core.accounts.api.user_api import UserSerializer


class ShareLinkRecipientPagination(PageNumberPagination):
    page_size = 12

    def get_paginated_response(self, data):
        data_response = {
            'page_size': self.page_size,
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        }
        return Response(data_response)


class ShareLinkRecipientListAPIView(RetrieveModelMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    pagination_class = ShareLinkRecipientPagination

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        return User.objects.filter(received_share_links__user_id=user_id,
                                   received_share_links__share_type='mixed').distinct()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def delete(self, request, *args, **kwargs):
        owner_id = self.kwargs.get('pk')
        recipient_id = int(self.kwargs.get('recipient_id'))

        if request.user.id != owner_id:
            return Response(
                {'detail': 'You do not have permission to remove recipients.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        through = ShareLink.recipients.through
        deleted_count, _ = through.objects.filter(
            sharelink__user_id=owner_id,
            sharelink__share_type='mixed',
            user_id=recipient_id,
        ).delete()

        return Response({'success': True, 'removed_from_share_links': deleted_count})


class ShareLinkRecipientListTypeArtworkAPIView(RetrieveModelMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    pagination_class = ShareLinkRecipientPagination

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        return User.objects.filter(received_share_links__user_id=user_id,
                                   received_share_links__share_type='artwork').distinct()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def delete(self, request, *args, **kwargs):
        owner_id = self.kwargs.get('pk')
        recipient_id = int(self.kwargs.get('recipient_id'))

        if request.user.id != owner_id:
            return Response(
                {'detail': 'You do not have permission to remove recipients.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        through = ShareLink.recipients.through
        deleted_count, _ = through.objects.filter(
            sharelink__user_id=owner_id,
            sharelink__share_type='artwork',
            user_id=recipient_id,
        ).delete()

        return Response({'success': True, 'removed_from_share_links': deleted_count})
