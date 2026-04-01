from django.contrib import admin


class UserPublicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'year', 'is_public')
    list_filter = ('year', 'user')
    search_fields = ('year', 'user', 'is_public')
