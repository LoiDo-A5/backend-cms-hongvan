import requests
from celery import shared_task
from django.core.files.base import ContentFile

from common.utils.hash import hash_bytes


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 5})
def update_facebook_user_avatar(user_id, access_token):
    from core.accounts.models import User

    user = User.objects.get(pk=user_id)
    fb_id = user.socialaccount_set.get(provider='facebook').uid

    avatar_res = requests.get(
        f'https://graph.facebook.com/{fb_id}/picture?'
        f'access_token={access_token}&type=large',
    )

    if not avatar_res.ok:
        return

    if not user.is_using_social_avatar:
        return

    social_avatar_hash = hash_bytes(avatar_res.content)
    if user.social_avatar_hash != social_avatar_hash:
        user.social_avatar_hash = social_avatar_hash
        user.save(update_fields=['social_avatar_hash'])

        user.avatar.save(f'user_{user.id}.jpg', ContentFile(avatar_res.content))
