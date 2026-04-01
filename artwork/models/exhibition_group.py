from django.db import models


class ExhibitionGroup(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    artworks = models.ManyToManyField('artwork.ArtWork', related_name='exhibition_groups')
    exhibition = models.ForeignKey(
        'artwork.Exhibition',
        on_delete=models.CASCADE,
        null=True,
        related_name='groups',
    )

    def __str__(self):  # pragma: nocover
        return self.title
