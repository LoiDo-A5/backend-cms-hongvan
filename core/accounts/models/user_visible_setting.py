from django.db import models


class UserVisibleSetting(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='visible_setting')
    is_public_profile = models.BooleanField(default=True)
    is_public_exhibition = models.BooleanField(default=True)
    is_public_artwork = models.BooleanField(default=True)
    is_public_follower = models.BooleanField(default=True)
    is_public_social_media = models.BooleanField(default=True)
    is_public_personal_info = models.BooleanField(default=True)

    def __str__(self):  # pragma: nocover
        return f'{self.user.id} | {self.user.name}'
