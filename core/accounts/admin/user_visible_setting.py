from django.contrib import admin


class UserVisibleSettingAdmin(admin.ModelAdmin):
    list_display = ('user',)
    list_filter = ('user',)
    search_fields = ('user',)
