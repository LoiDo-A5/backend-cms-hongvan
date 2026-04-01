from artwork.utils.const import STATUS_CHOICES


def update_field_status(Artwork):
    for artwork in Artwork.objects.exclude(status__in=dict(STATUS_CHOICES).keys()):
        artwork.status = ''
        artwork.save()
