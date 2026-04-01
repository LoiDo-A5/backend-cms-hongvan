from django.db import models
from django.utils.timezone import now

from artwork.utils.const import EXHIBITION_TYPE_CHOICES
from common.abstract_models.image_field import CustomImageField


class Exhibition(models.Model):
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, related_name='exhibitions')
    title = models.CharField(max_length=100)
    date_start = models.DateTimeField(null=False, blank=False)
    date_end = models.DateTimeField(null=False, blank=False)
    address = models.TextField(blank=True)
    curator = models.CharField(max_length=250, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EXHIBITION_TYPE_CHOICES, blank=True, null=True)
    cover_image = CustomImageField(blank=True, null=True)
    preface = models.TextField(max_length=6000, blank=True)
    organizer_name = models.CharField(max_length=200, blank=True, null=True)
    is_public = models.BooleanField(default=True)
    is_draft = models.BooleanField(default=False)

    def __str__(self):  # pragma: nocover
        return self.title

    def has_owner(self, user):
        return user.id == self.owner_id

    def has_ongoing(self):
        current_time = now()
        return self.date_start <= current_time <= self.date_end
