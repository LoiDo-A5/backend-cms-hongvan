from django.db import models
from core.accounts.models import User


class UserSignalId(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signal_ids')
    signal_id = models.UUIDField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
