def update_field_issued_by(ArtworkCertificate):
    for certificate in ArtworkCertificate.objects.all():
        artist = certificate.artwork_edition.artwork.artist
        certificate.issued_by = artist
        certificate.issued_to = artist
        certificate.save()
