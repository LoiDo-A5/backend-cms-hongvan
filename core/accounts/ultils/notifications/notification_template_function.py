from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE


def get_template_receive_certificate_request():
    from core.accounts.models import NotificationTemplate

    template, created = NotificationTemplate.objects.get_or_create(
        content_code=NOTIFICATIONS_CONTENT_CODE.RECEIVE_CERTIFICATE_REQUEST,
        defaults={
            'title_en': 'Gladius Art',
            'title_vi': 'Gladius Art',
            'content_en': '{request_user_name} requested a certificate of the artwork {artwork_title}.',
            'content_vi': '{request_user_name} đã yêu cầu tạo chứng nhận cho tác phẩm {artwork_title}.',
            'redirect': '/review-certificate-request/{certificate_request_id}',
        },
    )
    return template


def get_template_share_link_invitation():
    from core.accounts.models import NotificationTemplate

    template, created = NotificationTemplate.objects.get_or_create(
        content_code=NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION,
        defaults={
            'title_en': 'Gladius Art',
            'title_vi': 'Gladius Art',
            'content_en': '{from_user_name} shared a link with you: {share_link_title}.',
            'content_vi': '{from_user_name} đã chia sẻ một liên kết với bạn: {share_link_title}.',
            'redirect': '/share/{share_link_id}',
        },
    )
    return template


def get_template_share_link_invitation_no_title():
    from core.accounts.models import NotificationTemplate

    template, created = NotificationTemplate.objects.get_or_create(
        content_code=NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION_NO_TITLE,
        defaults={
            'title_en': 'Gladius Art',
            'title_vi': 'Gladius Art',
            'content_en': '{from_user_name} shared a link with you.',
            'content_vi': '{from_user_name} đã chia sẻ một liên kết với bạn.',
            'redirect': '/share/{share_link_id}',
        },
    )
    return template


def get_template_transfer_ownership_recipient():
    from core.accounts.models import NotificationTemplate

    template, created = NotificationTemplate.objects.get_or_create(
        content_code=NOTIFICATIONS_CONTENT_CODE.TRANSFER_OWNERSHIP_RECIPIENT,
        defaults={
            'title_en': 'Certificate Received Successfully.',
            'title_vi': 'Nhận Chứng Chỉ Thành Công.',
            'content_en': 'You have successfully received the Artwork Certificate for'
                          ' {artwork_title} from {from_user_name}.',
            'content_vi': 'Bạn đã nhận thành công Chứng nhận Tác phẩm cho {artwork_title} từ {from_user_name}.',
            'redirect': '/artwork-detail/{artwork_id}',
        },
    )
    return template


def get_template_approve_certificate_request():
    from core.accounts.models import NotificationTemplate

    template, created = NotificationTemplate.objects.get_or_create(
        content_code=NOTIFICATIONS_CONTENT_CODE.APPROVE_CERTIFICATE_REQUEST,
        defaults={
            'title_en': 'Gladius Art',
            'title_vi': 'Gladius Art',
            'content_en': 'A certificate for the artwork {artwork_title} was created by {issued_by_name}.',
            'content_vi': 'Chứng nhận cho tác phẩm {artwork_title} đã được tạo bởi {issued_by_name}.',
            'redirect': '/view-certificate/{certificate_code}',
        },
    )
    return template
