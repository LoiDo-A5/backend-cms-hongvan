from django.db import models

from common.abstract_models.image_field import CustomImageField
from core.accounts.models import UserAward


class ImageAward(models.Model):
    award = models.ForeignKey(UserAward, on_delete=models.CASCADE, null=True)
    image = CustomImageField(blank=False)
