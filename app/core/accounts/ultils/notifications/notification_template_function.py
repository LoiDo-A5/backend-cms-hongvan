from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE


def get_template_generic():
    from core.accounts.models import NotificationTemplate

    template, _ = NotificationTemplate.objects.get_or_create(
        content_code=NOTIFICATIONS_CONTENT_CODE.GENERIC,
        defaults={
            'title_en': 'Ward',
            'title_vi': 'Ward',
            'content_en': '{message}',
            'content_vi': '{message}',
            'redirect': '/',
        },
    )
    return template


def get_template_share_link():
    from core.accounts.models import NotificationTemplate

    template, _ = NotificationTemplate.objects.get_or_create(
        content_code=NOTIFICATIONS_CONTENT_CODE.SHARE_LINK,
        defaults={
            'title_en': 'Ward',
            'title_vi': 'Ward',
            'content_en': '{from_user_name} shared a link with you: {share_link_title}',
            'content_vi': '{from_user_name} đã chia sẻ một liên kết với bạn: {share_link_title}.',
            'redirect': '/share/{share_link_id}',
        },
    )
    return template


def get_template_share_link_no_title():
    from core.accounts.models import NotificationTemplate

    template, _ = NotificationTemplate.objects.get_or_create(
        content_code=NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_NO_TITLE,
        defaults={
            'title_en': 'Ward',
            'title_vi': 'Ward',
            'content_en': '{from_user_name} shared a link with you.',
            'content_vi': '{from_user_name} đã chia sẻ một liên kết với bạn.',
            'redirect': '/share/{share_link_id}',
        },
    )
    return template
