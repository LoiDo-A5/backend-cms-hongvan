def migrate_shared_items_to_artwork_field(ShareLink, ArtWork):
    share_links = ShareLink.objects.all()

    for share_link in share_links:
        artwork_ids = [
            item['id']
            for item in share_link.shared_items
            if item.get('type') == 'artwork'
        ]

        artworks = ArtWork.objects.filter(id__in=artwork_ids)
        share_link.artwork.set(artworks)
