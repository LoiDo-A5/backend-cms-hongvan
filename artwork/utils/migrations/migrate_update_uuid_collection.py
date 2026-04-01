import uuid

def update_field_uuid_collection(Collection):
    for collection in Collection.objects.all():
        collection.uuid = uuid.uuid4()
        collection.save()
