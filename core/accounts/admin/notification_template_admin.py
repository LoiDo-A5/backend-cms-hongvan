from django.contrib import admin


class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title_en',
        'content_en',
        'content_code',
    )

    search_fields = ['content_code', 'id']
