from django.contrib import admin


class OrientationArtworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'name_vi', 'category')
    list_filter = ('category',)
    search_fields = ('name',)
