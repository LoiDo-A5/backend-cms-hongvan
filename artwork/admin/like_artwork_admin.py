from django.contrib import admin


class LikeArtworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'artwork')
    list_filter = ('user', 'artwork')
    search_fields = ('id', 'user', 'artwork')
