from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.user import UserFactory
from core.accounts.models import User

from core.accounts.ultils.migrations.migrate_update_uuid_user import update_field_uuid_user


class MigrateUpdateUuidUserTests(TestCase):
    def test_migrate_update_uuid_user(self):
        user = UserFactory()
        user_2 = UserFactory()
        user_3 = UserFactory()
        user_4 = UserFactory()

        update_field_uuid_user(User)

        user.refresh_from_db()
        user_2.refresh_from_db()
        user_3.refresh_from_db()
        user_4.refresh_from_db()

        self.assertNotEqual(user.uuid, user_2.uuid)
        self.assertNotEqual(user.uuid, user_3.uuid)
        self.assertNotEqual(user.uuid, user_4.uuid)
        self.assertNotEqual(user_2.uuid, user_3.uuid)
        self.assertNotEqual(user_2.uuid, user_4.uuid)
        self.assertNotEqual(user_3.uuid, user_4.uuid)

