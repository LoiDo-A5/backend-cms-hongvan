from django.db import models


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super(ActiveManager, self).get_queryset().filter(active=True)


class AllQuerySet(models.QuerySet):
    pass


class ActiveModel(models.Model):
    active = models.BooleanField(default=True, db_index=True)

    objects = ActiveManager()
    all_objects = AllQuerySet.as_manager()

    def delete(self, using=None, keep_parents=False, hard=False):
        if hard:
            super(ActiveModel, self).delete(using=using, keep_parents=keep_parents)
        else:
            self.active = False
            self.save()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['id', 'active']),
        ]
