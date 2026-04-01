import re

from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile

from common.tasks import make_thumbnail
from django.db.models import FileField
from django.db.models.fields.files import FieldFile


class CustomImageFieldFile(ImageFieldFile):
    def __getattr__(self, item):
        if re.match(r'w\d{3,4}', item):  # w150, w375, w768, w1200
            return WrappedInstance(self, item)
        return super(CustomImageFieldFile, self).__getattr__(item)

    def save(self, name, content, save=True):
        super(CustomImageFieldFile, self).save(name=name, content=content, save=save)
        if self.field.widths:
            make_thumbnail.delay(self.name, self.field.widths)

    save.alters_data = True


class WrappedInstance:
    def __init__(self, obj: ImageFieldFile, width):
        self.obj = obj
        self.width = width

    @property
    def url(self):
        if not self.obj.name:
            return None

        url = self.obj.url
        path, name = url.rsplit('/', 1)
        return '/'.join([path, self.width, name])


class CustomImageField(ImageField):
    attr_class = CustomImageFieldFile

    def __init__(self, widths=None, *args, **kwargs):
        self.widths = widths or []
        super(CustomImageField, self).__init__(*args, **kwargs)


class CustomFileFieldFile(FieldFile):
    def __getattr__(self, item):
        if re.match(r'w\d{3,4}', item):  # w150, w375, w768, w1200
            return WrappedInstanceFieldFile(self, item)
        return super(CustomFileFieldFile, self).__getattr__(item)


class WrappedInstanceFieldFile:
    def __init__(self, obj: FieldFile, width):
        self.obj = obj
        self.width = width

    @property
    def url(self):
        if not self.obj.name:
            return None

        url = self.obj.url
        path, name = url.rsplit('/', 1)
        return '/'.join([path, self.width, name])


class CustomFileField(FileField):
    attr_class = CustomFileFieldFile

    def __init__(self, *args, **kwargs):
        super(CustomFileField, self).__init__(*args, **kwargs)
