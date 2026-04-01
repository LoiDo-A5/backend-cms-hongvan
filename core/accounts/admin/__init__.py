from django.contrib import admin
from rest_framework.authtoken.models import TokenProxy

from core.accounts.admin.notification_admin import NotificationAdmin
from core.accounts.admin.notification_template_admin import NotificationTemplateAdmin
from core.accounts.admin.saved_user_admin import SavedUserAdmin
from core.accounts.admin.token_admin import FilterTokenAdmin
from core.accounts.admin.user_admin import UserAdmin
from core.accounts.admin.user_award_admin import UserAwardAdmin
from core.accounts.admin.user_group_exhibition_admin import UserGroupExhibitionAdmin
from core.accounts.admin.user_invitation import UserInvitationAdmin
from core.accounts.admin.user_visible_setting import UserVisibleSettingAdmin
from core.accounts.admin.user_location_admin import UserLocationAdmin
from core.accounts.admin.user_publication_admin import UserPublicationAdmin
from core.accounts.admin.user_solo_exhibition_admin import UserSoloExhibitionAdmin
from core.accounts.admin.user_signal_admin import UserSignalIdAdmin
from core.accounts.admin.user_profile_admin import UserProfileAdmin
from core.accounts.models import User, Notification, NotificationTemplate
from core.accounts.models import UserLocation
from core.accounts.models import UserPublication
from core.accounts.models import UserSoloExhibition
from core.accounts.models import UserGroupExhibition
from core.accounts.models import UserSignalId
from core.accounts.models import UserAward
from core.accounts.models import UserProfile
from core.accounts.models import UserInvitation
from core.accounts.models import UserVisibleSetting
from core.accounts.models import SavedUser


admin.site.register(User, UserAdmin)
admin.site.register(UserSignalId, UserSignalIdAdmin)
admin.site.register(UserAward, UserAwardAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserSoloExhibition, UserSoloExhibitionAdmin)
admin.site.register(UserGroupExhibition, UserGroupExhibitionAdmin)
admin.site.register(UserPublication, UserPublicationAdmin)
admin.site.register(UserLocation, UserLocationAdmin)
admin.site.register(UserInvitation, UserInvitationAdmin)
admin.site.register(UserVisibleSetting, UserVisibleSettingAdmin)
admin.site.register(SavedUser, SavedUserAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)


admin.site.unregister(TokenProxy)
admin.site.register(TokenProxy, FilterTokenAdmin)
