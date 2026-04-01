from dj_rest_auth.registration.views import SocialAccountDisconnectView
from django.urls import include
from django.urls import path
from rest_framework import routers

from core.accounts.api.artist import ArtistViewSet
from core.accounts.api.delete_signal_id_api import DeleteSignalId
from core.accounts.api.notification import NotificationViewSet
from core.accounts.api.register.register_email import RegisterEmailApi
from core.accounts.api.saved_user import SavedUserApiView
from core.accounts.api.search_email_and_role import SearchUserByEmailAndRoleApi
from core.accounts.api.search_user import SearchUserApiView
from core.accounts.api.user_award import AwardViewSet
from core.accounts.api.change_language import ChangeLanguageApi
from core.accounts.api.change_password import ChangePasswordApi
from core.accounts.api.create_password import CreatePasswordApi
from core.accounts.api.user_collection import CollectionViewSet
from core.accounts.api.user_detail import UserDetailApi
from core.accounts.api.user_group_exhibition import GroupExhibitionViewSet
from core.accounts.api.user_invitation_api import UserInvitationApi
from core.accounts.api.user_publications import PublicationViewSet
from core.accounts.api.user_solo_exhibition import SoloExhibitionViewSet
from core.accounts.api.features import FeaturesApi
from core.accounts.api.forgot_password.forgot_password import ForgotPasswordApi
from core.accounts.api.forgot_password.forgot_password_set_password import ForgotPasswordSetPasswordApi
from core.accounts.api.forgot_password.forgot_password_verify_otp import ForgotPasswordVerifyOtpApi
from core.accounts.api.location import LocationApi
from core.accounts.api.login_api import LoginApi
from core.accounts.api.logout_api import LogoutApi
from core.accounts.api.me import MeApi
from core.accounts.api.user_profile import UserProfileApi
from core.accounts.api.referral_friends import ReferralFriendsApi
from core.accounts.api.register.register_phone import RegisterPhoneApi
from core.accounts.api.register.resend_otp import ResendOtpApi
from core.accounts.api.register.verify_otp import VerifyOtpApi
from core.accounts.api.register_signal_id_api import RegisterSignalIdApi
from core.accounts.api.social_login.facebook_login import FacebookLoginApi
from core.accounts.api.social_account import SocialAccountApi
from core.accounts.api.social_login.google_login import GoogleLoginApi
from core.accounts.api.social_login.send_otp import SocialSendOtpApi
from core.accounts.api.social_login.verify_otp import SocialVerifyOtpApi
from core.accounts.api.two_factor_verify import TFAVerifyView
from core.accounts.api.usable_password import UsablePasswordApi
from core.accounts.api.user_api import SearchUserByPhoneApi
from core.accounts.api.remove_background import MeRemoveBackgroundApi
from core.accounts.api.user_visible_setting import UserVisibleSettingApi
from core.accounts.api.search_user_gladius_id import SearchUserGladiusIDApiView

router = routers.SimpleRouter()
router.register(r'location', LocationApi)
router.register(r'award', AwardViewSet)
router.register(r'solo_exhibition', SoloExhibitionViewSet)
router.register(r'group_exhibition', GroupExhibitionViewSet)
router.register(r'publication', PublicationViewSet)
router.register(r'collection', CollectionViewSet)
router.register(r'artist', ArtistViewSet)
router.register(r'notification', NotificationViewSet)

urlpatterns = [
    path('login/', LoginApi.as_view()),
    path('logout/', LogoutApi.as_view()),
    path('change_password/', ChangePasswordApi.as_view()),
    path('create_password/', CreatePasswordApi.as_view()),
    path('forgot_password/', ForgotPasswordApi.as_view()),
    path('forgot_password/verify_otp/', ForgotPasswordVerifyOtpApi.as_view()),
    path('forgot_password/set_password/', ForgotPasswordSetPasswordApi.as_view()),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('login/facebook/', FacebookLoginApi.as_view()),
    path('login/google/', GoogleLoginApi.as_view()),
    path('social_accounts/', SocialAccountApi.as_view()),
    path('social_accounts/<int:pk>/disconnect/', SocialAccountDisconnectView.as_view()),
    path('login/social/send_otp/', SocialSendOtpApi.as_view()),
    path('login/social/verify/', SocialVerifyOtpApi.as_view()),
    path('me/', MeApi.as_view()),
    path('me/remove_background/', MeRemoveBackgroundApi.as_view()),
    path('profile/', UserProfileApi.as_view()),
    path('search/phone/<str:phone_number>/', SearchUserByPhoneApi.as_view()),
    path('register/phone/', RegisterPhoneApi.as_view()),
    path('register/verify_otp/', VerifyOtpApi.as_view()),
    path('register/resend_otp/', ResendOtpApi.as_view()),
    path('features/', FeaturesApi.as_view()),
    path('usable_password/', UsablePasswordApi.as_view()),
    path('register_signal_id/', RegisterSignalIdApi.as_view()),
    path('change_language/', ChangeLanguageApi.as_view()),
    path('referral_friends/', ReferralFriendsApi.as_view()),
    path('tfa_verify/', TFAVerifyView.as_view()),
    path('register/email/', RegisterEmailApi.as_view()),
    path('search_user/', SearchUserApiView.as_view()),
    path('user_invitation/', UserInvitationApi.as_view()),
    path('search_email_and_role/', SearchUserByEmailAndRoleApi.as_view()),
    path('user_visible_setting/', UserVisibleSettingApi.as_view()),
    path('user_details/', UserDetailApi.as_view()),
    path('saved_user/', SavedUserApiView.as_view()),
    path('delete_signal_id/', DeleteSignalId.as_view()),
    path('search_user_gladius_id/', SearchUserGladiusIDApiView.as_view()),
]

urlpatterns += router.urls
