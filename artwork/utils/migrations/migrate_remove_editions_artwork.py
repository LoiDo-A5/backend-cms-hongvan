def remove_editions_artwork(ArtworkEdition):
    ArtworkEdition.objects.filter(edition_number__gt=20).delete()

def update_artwork_total_edition(Artwork):
    Artwork.objects.filter(total_edition__gt=20).update(total_edition=20)