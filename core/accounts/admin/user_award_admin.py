from django.contrib import admin

from core.accounts.models import ImageAward


class ImageAwardInline(admin.StackedInline):
    model = ImageAward
    can_delete = True
    verbose_name_plural = 'Images Award'
    fields = ('image',)
    show_change_link = True


class UserAwardAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'year', 'is_public')
    list_filter = ('year', 'user')
    search_fields = ('year', 'user', 'is_public')

    inlines = [
        ImageAwardInline,
    ]
