from django.db import models


class UserGroupExhibition(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='group_exhibitions')
    year = models.IntegerField(blank=True, null=True)
    to_year = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=1000)
    is_public = models.BooleanField(default=True)
    exhibition_link = models.URLField(blank=True, null=True)

    def __str__(self):  # pragma: nocover
        return f'Group Exhibition for {self.user.name} in {self.year}'
