def update_field_is_first_login(User):
    User.objects.update(is_first_login=False)

