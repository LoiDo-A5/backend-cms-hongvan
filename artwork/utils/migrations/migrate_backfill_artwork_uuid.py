import uuid


def backfill_artwork_uuid(ArtWork):
    for art in ArtWork.objects.filter(uuid__isnull=True).iterator():
        art.uuid = uuid.uuid4()
        art.save(update_fields=['uuid'])
