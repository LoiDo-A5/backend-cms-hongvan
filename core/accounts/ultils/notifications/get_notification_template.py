from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE
from core.accounts.ultils.notifications.notification_template_function import (
    get_template_generic,
    get_template_share_link,
    get_template_share_link_no_title,
)

NOTIFICATION_TEMPLATE_MAP = {
    NOTIFICATIONS_CONTENT_CODE.GENERIC: get_template_generic,
    NOTIFICATIONS_CONTENT_CODE.SHARE_LINK: get_template_share_link,
    NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_NO_TITLE: get_template_share_link_no_title,
}


def get_notification_template(content_code):
    template_function = NOTIFICATION_TEMPLATE_MAP.get(content_code, None)

    if not template_function:
        return None

    return template_function()
