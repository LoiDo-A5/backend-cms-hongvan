from io import StringIO
from django.core.files import File

from core.accounts.tests.api.base_user_test import BaseUserTest


class MeRemoveBackgroundApiTest(BaseUserTest):
    def test_user_remove_background(self):
        file_content = StringIO()
        background = File(file_content, 'mock-file')

        self.user.background = background
        self.user.save()

        response = self.client.post('/api/accounts/me/remove_background/')

        self.user.refresh_from_db()
        self.assertIsNone(response.data['background'])
