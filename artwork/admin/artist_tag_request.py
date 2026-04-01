from django.contrib import admin


class ArtistTagRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'artwork', 'request_by', 'request_to', 'status')
    list_filter = ('request_by', 'request_to', 'artwork')
    search_fields = ('request_by',)
