from django.contrib import admin


class StyleArtworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'name_vi', 'category', 'user')
    list_filter = ('category', 'user')
    search_fields = ('name',)
