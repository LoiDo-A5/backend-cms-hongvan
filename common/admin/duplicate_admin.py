import uuid

from django.contrib import admin
from django.contrib import messages
from django.db import models


class DuplicateAdmin(admin.ModelAdmin):
    def get_actions(self, request):
        return {**super().get_actions(request), 'duplicate_items': self.get_action('duplicate_items')}

    def prepare_duplicate_object(self, instance):
        return instance

    def related_objects(self, instance):
        fields = instance._meta.get_fields()
        related_objects_to_duplicate = []

        for field in fields:
            if isinstance(field, models.fields.UUIDField):
                setattr(instance, field.name, uuid.uuid4())
            if field.one_to_one:
                setattr(instance, field.name, None)
            if field.one_to_many:
                related_object_manager = getattr(instance, field.name, None)
                if related_object_manager:
                    related_objects = list(related_object_manager.all())
                    related_objects_to_duplicate += related_objects

        return list(set(related_objects_to_duplicate))

    def duplicate_object(self, instance):
        related_objects_to_duplicate = self.related_objects(instance)

        instance.pk = None
        self.prepare_duplicate_object(instance)
        instance.save()

        for related_object in related_objects_to_duplicate:
            for field in related_object._meta.fields:
                if field.related_model == instance._meta.model:
                    setattr(related_object, field.name, instance)
            self.duplicate_object(related_object)

        return instance

    def duplicate_items(self, request, queryset):
        for obj in queryset:
            new_obj = self.duplicate_object(obj)
            messages.success(request, f'Copy {obj} to {new_obj} successful!')
