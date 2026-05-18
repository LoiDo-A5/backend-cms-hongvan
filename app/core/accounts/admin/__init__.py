from django.contrib import admin
from rest_framework.authtoken.models import TokenProxy

from core.accounts.admin.notification_admin import NotificationAdmin
from core.accounts.admin.notification_template_admin import NotificationTemplateAdmin
from core.accounts.admin.token_admin import FilterTokenAdmin
from core.accounts.admin.user_admin import UserAdmin
from core.accounts.admin.user_signal_admin import UserSignalIdAdmin
from core.accounts.admin.user_profile_admin import UserProfileAdmin
from core.accounts.models import Notification, NotificationTemplate, User, UserProfile, UserSignalId

admin.site.register(User, UserAdmin)
admin.site.register(UserSignalId, UserSignalIdAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)

admin.site.unregister(TokenProxy)
admin.site.register(TokenProxy, FilterTokenAdmin)
