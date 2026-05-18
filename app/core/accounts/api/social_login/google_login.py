from io import BytesIO
from uuid import uuid4

import requests

from common.utils.hash import hash_bytes
from core.accounts.api.social_login.social_login import SocialLoginApi
from core.accounts.custom_providers.custom_google.views import CustomGoogleOAuth2Adapter


class GoogleLoginApi(SocialLoginApi):
    adapter_class = CustomGoogleOAuth2Adapter

    def process_login(self):
        super(GoogleLoginApi, self).process_login()

        if not self.user.is_using_social_avatar:
            return
        login = self.serializer.validated_data['login']
        avatar_response = requests.get(login.account.extra_data['picture'])
        if not avatar_response.ok:
            return

        social_avatar_hash = hash_bytes(avatar_response.content)
        if self.user.social_avatar_hash == social_avatar_hash:
            return

        self.user.avatar.save(f'avatar_{self.user.id}_{uuid4()}.jpg', BytesIO(avatar_response.content))
        self.user.social_avatar_hash = social_avatar_hash
        self.user.save()
