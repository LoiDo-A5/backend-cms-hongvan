def update_owner_field_artwork(ArtWork):
    for artwork in ArtWork.objects.filter(owner__isnull=True):
        artwork.owner = artwork.artist
        artwork.save()
