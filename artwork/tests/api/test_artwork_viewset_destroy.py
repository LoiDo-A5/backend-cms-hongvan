from types import SimpleNamespace

from rest_framework.exceptions import PermissionDenied

from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.api.artwork import ArtworkViewSet


class DummyInstance:
    def __init__(self, owner_id):
        self._owner_id = owner_id
        self.deleted = False

    def has_owner(self, user):
        return getattr(user, 'id', None) == self._owner_id

    def __setattr__(self, name, value):
        if name == '_current_user' and hasattr(self, 'raise_on_set') and self.raise_on_set:
            raise Exception('fail set')
        return super().__setattr__(name, value)

    def delete(self):
        self.deleted = True


class ArtworkViewSetDestroyTest(BaseUserTest):
    def get_view(self):
        view = ArtworkViewSet()
        view.request = SimpleNamespace(user=self.user)
        return view

    def test_perform_destroy_sets_current_user_when_possible(self):
        inst = DummyInstance(owner_id=self.user.id)
        view = self.get_view()
        view.perform_destroy(inst)
        self.assertTrue(inst.deleted)
        self.assertEqual(getattr(inst, '_current_user'), self.user)

    def test_perform_destroy_passes_when_setting_current_user_fails(self):
        inst = DummyInstance(owner_id=self.user.id)
        inst.raise_on_set = True
        view = self.get_view()
        view.perform_destroy(inst)
        self.assertTrue(inst.deleted)

    def test_perform_destroy_permission_denied_for_non_owner(self):
        inst = DummyInstance(owner_id=-1)
        view = self.get_view()
        with self.assertRaises(PermissionDenied):
            view.perform_destroy(inst)
