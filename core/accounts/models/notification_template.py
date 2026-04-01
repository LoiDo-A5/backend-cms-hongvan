from django.db import models


class NOTIFICATIONS_CONTENT_CODE:
    RECEIVE_CERTIFICATE_REQUEST = 'RECEIVE_CERTIFICATE_REQUEST'
    TRANSFER_OWNERSHIP_RECIPIENT = 'TRANSFER_OWNERSHIP_RECIPIENT'
    SHARE_LINK_INVITATION = 'SHARE_LINK_INVITATION'
    SHARE_LINK_INVITATION_NO_TITLE = 'SHARE_LINK_INVITATION_NO_TITLE'
    APPROVE_CERTIFICATE_REQUEST = 'APPROVE_CERTIFICATE_REQUEST'


CONTENT_CODE_NOTIFICATIONS = (
    (NOTIFICATIONS_CONTENT_CODE.RECEIVE_CERTIFICATE_REQUEST, 'RECEIVE_CERTIFICATE_REQUEST'),
    (NOTIFICATIONS_CONTENT_CODE.TRANSFER_OWNERSHIP_RECIPIENT, 'TRANSFER_OWNERSHIP_RECIPIENT'),
    (NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION, 'SHARE_LINK_INVITATION'),
    (NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION_NO_TITLE, 'SHARE_LINK_INVITATION_NO_TITLE'),
    (NOTIFICATIONS_CONTENT_CODE.APPROVE_CERTIFICATE_REQUEST, 'APPROVE_CERTIFICATE_REQUEST'),
)


class NotificationTemplate(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    content_code = models.CharField(max_length=100, choices=CONTENT_CODE_NOTIFICATIONS, null=True, blank=True)
    title_en = models.CharField(max_length=255, null=True, blank=True)
    title_vi = models.CharField(max_length=255, null=True, blank=True)
    content_en = models.CharField(max_length=355, null=True, blank=True)
    content_vi = models.CharField(max_length=355, null=True, blank=True)
    redirect = models.CharField(max_length=355)

    def get_format_content(self, params, lang='en'):
        content = getattr(self, f'content_{lang}', self.content_en)

        try:
            return content.format(**params)
        except KeyError:
            return content

    def get_redirect_url(self, params):
        try:
            return self.redirect.format(**params)
        except KeyError:
            return self.redirect
