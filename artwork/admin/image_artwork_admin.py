from django.contrib import admin


class ImageArtworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'artwork', 'image')
    list_filter = ('artwork',)
    search_fields = ('artwork__title',)

    def save_model(self, request, obj, form, change):
        if request and request.user and request.user.is_authenticated:
            obj._current_user = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if request and request.user and request.user.is_authenticated:
            obj._current_user = request.user
        super().delete_model(request, obj)
