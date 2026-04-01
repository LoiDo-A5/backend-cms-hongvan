from django.test import TestCase

from artwork.factories.share_link import ShareLinkFactory


class ShareLinkModelTests(TestCase):
    def test_str_includes_user_and_share_type(self):
        share_link = ShareLinkFactory(share_type='artwork')

        value = str(share_link)

        self.assertIn(str(share_link.id), value)
        self.assertIn(share_link.user.name, value)
        self.assertIn(share_link.share_type, value)

    def test_validate_password_returns_true_when_no_password_set(self):
        share_link = ShareLinkFactory(password=None)

        self.assertTrue(share_link.validate_password('anything'))

    def test_get_share_url_without_request_returns_relative_path(self):
        share_link = ShareLinkFactory()

        self.assertEqual(share_link.get_share_url(), f'/api/artwork/share/{share_link.id}/')
