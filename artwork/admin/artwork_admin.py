from django.contrib import admin

from artwork.models import ImageArtwork
from artwork.models.artwork import ArtWork
from core.accounts.models.user import USER_ROLE


class ImageArtworkInline(admin.StackedInline):
    model = ImageArtwork
    can_delete = False
    verbose_name_plural = 'Images Artwork'
    fields = ('image',)
    show_change_link = True


class ArtWorkAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'title', 'owner', 'category', 'style', 'subject', 'color', 'medium',
                    'orientation', 'created_at')
    list_filter = ('category', 'style', 'subject', 'artist', 'color', 'medium',
                   'orientation', 'owner')
    search_fields = ('title', 'artist__username', 'uuid')

    autocomplete_fields = ['artist', 'style', 'subject', 'color', 'medium',
                           'orientation']
    exclude = ('color',)

    inlines = [
        ImageArtworkInline,
    ]

    readonly_fields = ('uuid', 'created_at', 'updated_at')
    filter_horizontal = ('subjects',)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['total_edition'] + list(super().get_readonly_fields(request, obj))
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request):
        return ArtWork.all_objects.all()

    def save_model(self, request, obj, form, change):
        if request and request.user and request.user.is_authenticated:
            obj._current_user = request.user

        super().save_model(request, obj, form, change)

        if change and request and getattr(request.user, 'role', None) == USER_ROLE.ARTIST:
            if 'description' in getattr(form, 'changed_data', []):
                new_description = obj.description
                for linked in obj.linked_artworks.all():
                    linked._current_user = request.user
                    linked.description = new_description
                    linked.save()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for instance in instances:
            if isinstance(instance, ImageArtwork):
                instance._current_user = request.user
            instance.save()

        for obj in formset.deleted_objects:
            if isinstance(obj, ImageArtwork):
                obj._current_user = request.user
            obj.delete()

        formset.save_m2m()

    def delete_model(self, request, obj):
        try:
            if request and getattr(request, 'user', None) and request.user.is_authenticated:
                obj._current_user = request.user
        except Exception:
            pass
        super().delete_model(request, obj)
