from django.shortcuts import get_object_or_404
from rest_framework.exceptions import (
    PermissionDenied,
    AuthenticationFailed,
    NotAuthenticated,
)

from artwork.models import ShareLink


class ShareLinkValidateMixin:
    def get_share_link(self, share_link_id):
        return get_object_or_404(
            ShareLink,
            pk=share_link_id,
        )

    def validate_status(self, share_link):
        if not share_link.is_valid:
            raise PermissionDenied('This share link is no longer valid')

    def validate_password(self, share_link, password):
        if not share_link.password:
            return

        if not password:
            raise AuthenticationFailed(
                {
                    'error': 'Password required',
                    'requires_password': True,
                },
            )

        if not share_link.validate_password(password):
            raise AuthenticationFailed(
                {
                    'error': 'Invalid password',
                },
            )

    def validate_recipient(self, share_link, request):
        user = request.user

        if getattr(user, 'is_authenticated', False):
            is_owner = share_link.user_id == user.id
            if is_owner:
                return

        if share_link.recipient_type not in ['specific', 'both']:
            return

        if not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated(
                {
                    'error': 'Login required',
                    'requires_login': True,
                },
            )

        is_recipient = share_link.recipients.filter(id=user.id).exists()
        if not is_recipient:
            raise PermissionDenied(
                'You do not have permission to access this share link',
            )

    def validate_share_link(
        self,
        share_link_id,
        request,
        password=None,
    ):
        share_link = self.get_share_link(share_link_id)

        self.validate_status(share_link)
        self.validate_password(share_link, password)
        self.validate_recipient(share_link, request)

        return share_link


class ShareLinkArtworkMixin(ShareLinkValidateMixin):
    def get_shared_artworks(self, request, share_link_id):
        share_link = self.validate_share_link(
            share_link_id=share_link_id,
            request=request,
            password=request.query_params.get('password'),
        )

        artworks = share_link.get_shared_artworks()
        return artworks


class ShareLinkCollectionMixin(ShareLinkValidateMixin):
    def get_shared_collections(self, request, share_link_id):
        share_link = self.validate_share_link(
            share_link_id=share_link_id,
            request=request,
            password=request.query_params.get('password'),
        )

        collections = share_link.get_shared_collections()
        return collections
