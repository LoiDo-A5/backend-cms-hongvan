from django.db import models
from django.contrib.postgres.fields import ArrayField
from common.abstract_models.image_field import CustomImageField


class UserProfile(models.Model):
    image_portrait = CustomImageField(blank=True, null=True)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='profile')
    nick_name = models.CharField(max_length=50, blank=True, null=True)
    id_card_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(max_length=100, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    live_at = models.CharField(max_length=200, blank=True, null=True)

    # Artist
    certification = models.CharField(max_length=1000, blank=True, null=True)
    introduction = models.TextField(max_length=6000, blank=True, null=True)
    websites = ArrayField(models.CharField(), default=list, null=True, blank=True)
    socials = ArrayField(models.JSONField(default=dict), default=list, null=True, blank=True)
    about_artist = models.TextField(max_length=10000, blank=True, null=True)
    membership = ArrayField(models.JSONField(default=dict), default=list, null=True, blank=True)
    training_background = ArrayField(models.JSONField(default=dict), default=list, null=True, blank=True)
    year_of_birth = models.CharField(null=True, blank=True)
    place_of_birth = models.CharField(null=True, blank=True)
    signature = CustomImageField(blank=True, null=True)

    def has_owner(self, user):
        return user.id == self.user_id
