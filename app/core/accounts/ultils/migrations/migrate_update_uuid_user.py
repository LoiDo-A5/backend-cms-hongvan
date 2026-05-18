import uuid

def update_field_uuid_user(User):
    for user in User.objects.all():
        user.uuid = uuid.uuid4()
        user.save()
