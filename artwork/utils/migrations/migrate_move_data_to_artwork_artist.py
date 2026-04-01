def move_data_to_artwork_artist(ArtWork, ArtworkArtist):
    for artwork in ArtWork.objects.all():
        artist_name = artwork.artist_name
        contact_info = artwork.contact_info_artist
        year_of_birth = artwork.year_of_birth_artist

        existing_artist_artwork = ArtworkArtist.objects.filter(
            artist_name=artist_name,
            year_of_birth=year_of_birth,
            create_user=artwork.owner,
        ).first()

        if existing_artist_artwork:
            artwork.artist_artwork = existing_artist_artwork
            artwork.save()
        elif artist_name:
            artist_artwork = ArtworkArtist.objects.create(
                artist_name=artist_name,
                contact_info=contact_info,
                year_of_birth=year_of_birth,
                create_user=artwork.owner
            )
            artwork.artist_artwork = artist_artwork
            artwork.save()
