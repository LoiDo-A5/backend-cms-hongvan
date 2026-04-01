from django.db import models
from core.accounts.models import User


class SavedUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_by')
    saved_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_users', null=True, blank=True)
    name_saved_user = models.CharField(max_length=80, blank=True, null=True)
    contact_info_saved_user = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    year_of_birth = models.CharField(null=True, blank=True)
    connected_artist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connected_artists',
                                         null=True, blank=True)
