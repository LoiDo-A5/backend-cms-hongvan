from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE
from core.accounts.ultils.notifications.notification_template_function import (
    get_template_receive_certificate_request,
    get_template_transfer_ownership_recipient,
    get_template_share_link_invitation,
    get_template_share_link_invitation_no_title,
    get_template_approve_certificate_request,
)

NOTIFICATION_TEMPLATE_MAP = {
    NOTIFICATIONS_CONTENT_CODE.RECEIVE_CERTIFICATE_REQUEST: get_template_receive_certificate_request,
    NOTIFICATIONS_CONTENT_CODE.TRANSFER_OWNERSHIP_RECIPIENT: get_template_transfer_ownership_recipient,
    NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION: get_template_share_link_invitation,
    NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION_NO_TITLE: get_template_share_link_invitation_no_title,
    NOTIFICATIONS_CONTENT_CODE.APPROVE_CERTIFICATE_REQUEST: get_template_approve_certificate_request,
}


def get_notification_template(content_code):
    template_function = NOTIFICATION_TEMPLATE_MAP.get(content_code, None)

    if not template_function:
        return None

    return template_function()
