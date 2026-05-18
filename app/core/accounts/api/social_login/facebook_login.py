from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter

from core.accounts.api.social_login.social_login import SocialLoginApi
from core.accounts.tasks import update_facebook_user_avatar


class FacebookLoginApi(SocialLoginApi):
    adapter_class = FacebookOAuth2Adapter

    def process_login(self):
        super(FacebookLoginApi, self).process_login()
        update_facebook_user_avatar.delay(self.user.id, self.serializer.validated_data['access_token'])
