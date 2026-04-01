from celery import shared_task

from artwork.models import ArtWork
from artwork.models.artwork_certificate import ArtworkCertificate
from core.accounts.models import User
from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE
from core.accounts.tasks.notification import make_notification_message


@shared_task
def notify_receive_request_certificate(receive_user_id, request_user_id, artwork_id, certificate_request_id):
    receive_user = User.objects.get(pk=receive_user_id)
    request_user = User.objects.get(pk=request_user_id)
    artwork = ArtWork.objects.get(pk=artwork_id)

    make_notification_message(
        user=receive_user,
        content_code=NOTIFICATIONS_CONTENT_CODE.RECEIVE_CERTIFICATE_REQUEST,
        content_params={
            'request_user_name': request_user.name,
            'artwork_title': artwork.title,
            'certificate_request_id': certificate_request_id,
        },
        notification_kwargs={
            'icon': request_user.avatar,
        },
        push_kwargs={
            'data': {
                'content_code': NOTIFICATIONS_CONTENT_CODE.RECEIVE_CERTIFICATE_REQUEST,
                'params': {
                    'certificate_request_id': certificate_request_id,
                },
            },
        },
        credentials=None,
    )


@shared_task
def notify_approve_certificate_request(request_user_id, issued_by_user_id, artwork_id, certificate_id):
    request_user = User.objects.get(pk=request_user_id)
    issued_by_user = User.objects.get(pk=issued_by_user_id)
    artwork = ArtWork.objects.get(pk=artwork_id)
    certificate = ArtworkCertificate.objects.get(pk=certificate_id)

    make_notification_message(
        user=request_user,
        content_code=NOTIFICATIONS_CONTENT_CODE.APPROVE_CERTIFICATE_REQUEST,
        content_params={
            'artwork_title': artwork.title,
            'certificate_code': str(certificate.code),
            'issued_by_name': getattr(issued_by_user, 'name', ''),
            'artwork_id': artwork_id,
        },
        notification_kwargs={
            'icon': getattr(issued_by_user, 'avatar', None),
        },
        push_kwargs={
            'data': {
                'content_code': NOTIFICATIONS_CONTENT_CODE.APPROVE_CERTIFICATE_REQUEST,
                'params': {
                    'certificate_code': str(certificate.code),
                    'artwork_id': artwork_id,
                },
            },
        },
        credentials=None,
    )
