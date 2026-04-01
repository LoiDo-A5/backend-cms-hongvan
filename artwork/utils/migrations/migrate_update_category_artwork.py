from django.db import transaction


def update_category_artwork(ArtWork, ColorArtwork, MediumArtwork, OrientationArtwork, SizeArtwork, StyleArtwork,
                            SubjectArtwork):
    with transaction.atomic():
        models = [
            ArtWork, ColorArtwork, MediumArtwork, OrientationArtwork, SizeArtwork, StyleArtwork, SubjectArtwork
        ]

        for model in models:
            if model:
                model.objects.update(category='painting')
