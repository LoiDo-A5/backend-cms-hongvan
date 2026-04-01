def create_editions_artwork(Artwork, ArtworkEdition):
    artworks = Artwork.objects.all()

    for artwork in artworks:
        total_edition = artwork.total_edition
        exist_edition = artwork.editions.count()

        for x in range(exist_edition, total_edition):
            ArtworkEdition.objects.create(
                artwork=artwork,
                edition_number=x+1
            )