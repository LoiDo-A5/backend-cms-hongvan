from django.contrib import admin

from core.accounts.models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'user_uuid')
    search_fields = ['user__username']
    autocomplete_fields = ['user']

    def user_uuid(self, obj):
        return obj.user.uuid if obj.user else None
    user_uuid.admin_order_field = 'user__uuid'
    user_uuid.short_description = 'User UUID'
