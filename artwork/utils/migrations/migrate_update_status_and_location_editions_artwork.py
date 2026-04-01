def update_status_and_location_editions_artwork(ArtworkEdition):
    for edition in ArtworkEdition.objects.all():
        artwork = edition.artwork

        if artwork:
            edition.status = artwork.status if artwork.status is not None else None
            edition.location = artwork.location if artwork.location is not None else None

            edition.save()
