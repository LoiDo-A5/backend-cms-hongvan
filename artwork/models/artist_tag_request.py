from django.db import models

from artwork.utils.const import STATUS_REQUEST_CHOICES, STATUS_REQUEST


class ArtistTagRequest(models.Model):
    artwork = models.ForeignKey('artwork.ArtWork', on_delete=models.CASCADE,
                                related_name='tag_request')
    request_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                   related_name='artist_tag_requests_made')
    request_to = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                   related_name='artist_tag_requests_received')
    status = models.IntegerField(choices=STATUS_REQUEST_CHOICES,
                                 blank=True, null=True, default=STATUS_REQUEST.REQUEST_RECEIVED)
    message = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
