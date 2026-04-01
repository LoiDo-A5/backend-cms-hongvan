def update_subject_to_subjects(Artwork):
    for artwork in Artwork.objects.all():
        if artwork.subject:
            artwork.subjects.add(artwork.subject)
            artwork.save()
