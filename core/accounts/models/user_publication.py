from django.db import models


class UserPublication(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='publications')
    year = models.IntegerField(null=True, blank=True)
    description = models.CharField(max_length=1000)
    is_public = models.BooleanField(default=True)

    def __str__(self):  # pragma: nocover
        return f'Publication for {self.user.name} in {self.year}'
