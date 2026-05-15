from django.conf import settings
from django.db import models

from common.abstract_models.active_model import ActiveModel
from common.abstract_models.image_field import CustomImageField


class Project(ActiveModel):
    name = models.CharField(max_length=255, db_index=True)
    is_visible = models.BooleanField(default=True, db_index=True)
    website_card_title = models.CharField(max_length=255, blank=True)
    website_card_content = models.TextField(blank=True)
    website_card_thumbnail = CustomImageField(blank=True, null=True)
    hero_title = models.CharField(max_length=255, blank=True)
    hero_content = models.TextField(blank=True)
    hero_image = CustomImageField(blank=True, null=True)
    section_background_image = CustomImageField(blank=True, null=True)
    features = models.JSONField(default=list, blank=True)
    cta_title = models.CharField(max_length=255, blank=True)
    cta_content = models.TextField(blank=True)
    cta_button_label = models.CharField(max_length=255, blank=True)
    cta_button_url = models.URLField(blank=True)
    long_description_title = models.CharField(max_length=255, blank=True)
    long_description = models.TextField(blank=True)
    accordion_title = models.CharField(max_length=255, blank=True)
    accordion_background_image = CustomImageField(blank=True, null=True)
    accordion_items = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_projects',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_projects',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']
        verbose_name = 'Dự án'
        verbose_name_plural = 'Dự án'
        indexes = [
            models.Index(fields=['id', 'active']),
        ]

    def __str__(self):
        return self.name