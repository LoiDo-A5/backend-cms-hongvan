from django.db import models


USER_ACTION_UPDATE_GLADIUS_ID = 'user_gladius_id_updated'

USER_ACTION_CHOICES = [
    (USER_ACTION_UPDATE_GLADIUS_ID, 'User Gladius ID Updated'),
]


class UserLog(models.Model):
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        help_text='User this log entry is related to',
    )
    action_type = models.CharField(
        max_length=50,
        choices=USER_ACTION_CHOICES,
        help_text='Type of action performed',
    )
    template_vi = models.TextField(
        null=True,
        blank=True,
        help_text='Vietnamese template at the time of logging',
    )
    template_en = models.TextField(
        null=True,
        blank=True,
        help_text='English template at the time of logging',
    )
    content_vi = models.TextField(
        default='',
        help_text='Snapshot Vietnamese content at the time of logging',
    )
    content_en = models.TextField(
        default='',
        help_text='Snapshot English content at the time of logging',
    )
    params = models.JSONField(
        default=dict,
        blank=True,
        help_text='Arbitrary parameters snapshot (e.g., old/new values, field names)',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this action was performed',
    )

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):  # pragma: nocover
        return f'[{self.created_at}] User {getattr(self.user, "id", "?")}: {self.action_type}'
