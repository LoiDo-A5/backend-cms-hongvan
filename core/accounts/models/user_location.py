from django.db import models


class UserLocation(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='locations')
    location = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):  # pragma: nocover
        return str(self.location)
