def update_signature_artwork_certificate(ArtworkCertificate, UserProfile):
    artwork_certificates = ArtworkCertificate.objects.filter(signature__in=[None, ''])
    for certificate in artwork_certificates:
        user_profile = UserProfile.objects.filter(user=certificate.artwork_edition.artwork.artist).first()
        if user_profile and user_profile.signature:
            certificate.signature = user_profile.signature
            certificate.save()

