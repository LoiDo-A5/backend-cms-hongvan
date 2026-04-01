from django.db import models


class UserCollection(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='profile_collections')
    name = models.CharField(max_length=1000)
    is_public = models.BooleanField(default=True)

    def __str__(self):  # pragma: nocover
        return f'{self.name}'
