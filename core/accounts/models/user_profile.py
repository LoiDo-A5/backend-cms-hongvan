from django.db import models

from common.abstract_models.image_field import CustomImageField


class UserProfile(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='profile')
    nick_name = models.CharField(max_length=50, blank=True, null=True)
    id_card_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(max_length=500, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    live_at = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(max_length=2000, blank=True, null=True)
    image_portrait = CustomImageField(blank=True, null=True)

    def has_owner(self, user):
        return user.id == self.user_id
