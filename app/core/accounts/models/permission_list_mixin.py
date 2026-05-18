from django.db import models

PERMISSION_FIELDS = tuple()


class PermissionListMixin(models.Model):
    for field in PERMISSION_FIELDS:  # pragma: nocover until PERMISSION_FIELDS is not empty
        locals()[field] = models.IntegerField(default=0)

    class Meta:
        abstract = True
