from django.contrib import admin


class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
    )

    search_fields = ['content_code', 'id']
