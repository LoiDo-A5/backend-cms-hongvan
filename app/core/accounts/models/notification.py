from django.db import models

from common.abstract_models.image_field import CustomImageField
from core.accounts.models.notification_template import CONTENT_CODE_NOTIFICATIONS


class Notification(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey('accounts.NotificationTemplate', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)

    content_code = models.CharField(max_length=100, choices=CONTENT_CODE_NOTIFICATIONS, null=True, blank=True)
    params = models.JSONField(default=dict, blank=True)
    push_kwargs = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    icon = CustomImageField(null=True)

    class Meta:
        ordering = ('-created_at',)

    def get_formatted_content(self, lang):
        if not self.template:
            return ''

        return self.template.get_format_content(params=self.params, lang=lang)

    @property
    def redirect_url(self):
        if not self.template:
            return ''

        return self.template.get_redirect_url(self.params)

    @property
    def content_en(self):
        return self.get_formatted_content(lang='en')

    @property
    def content_vi(self):
        return self.get_formatted_content(lang='vi')
