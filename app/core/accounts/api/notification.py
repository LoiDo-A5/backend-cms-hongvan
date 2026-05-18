from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response

from core.accounts.models.notification import Notification
from core.accounts.serializers.notification import NotificationSerializer, NotificationNumber


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.notifications.all()

    def get_serializer_class(self):
        if self.action == 'number':
            return NotificationNumber
        return NotificationSerializer

    @action(detail=True, methods=['POST'])
    def set_read(self, request, *args, **kwargs):
        notification = self.get_object()

        if notification.is_read:
            return Response(status=status.HTTP_204_NO_CONTENT)

        notification.is_read = True
        notification.save()
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def number(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unread_queryset = queryset.filter(is_read=False)
        unread = unread_queryset.count()

        data = {'unread': unread, 'unseen': 0}

        user = request.user
        last_seen_at = user.last_seen_notification_at
        if not last_seen_at:
            data['unseen'] = unread
        else:
            unseen_queryset = queryset.filter(created_at__gte=last_seen_at, is_read=False)
            data['unseen'] = unseen_queryset.count()
        serializer = self.get_serializer(instance=data)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'])
    def set_last_seen(self, request, *args, **kwargs):
        user = request.user
        user.last_seen_notification_at = timezone.now()
        user.save()
        return Response(status=status.HTTP_200_OK)
