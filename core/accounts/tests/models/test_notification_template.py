from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.notification_template import NotificationTemplateFactory


class NotificationTemplateTest(TestCase):
    def test_notification_template_format_content(self):
        content_en = '{user_name} like this post'
        content_vi = '{user_name} thich post nay'
        params = {
            'user_name': 'John',
            'user_id': 1,
            'post_id': 2,
        }
        template = NotificationTemplateFactory(content_en=content_en, content_vi=content_vi)

        content = template.get_format_content(params)
        self.assertEqual(content, 'John like this post')

        content_vi = template.get_format_content(params, 'vi')
        self.assertEqual(content_vi, 'John thich post nay')

    def test_notification_template_should_return_default_content_if_missing_params(self):
        content_en = '{user_name} like this post'
        content_vi = '{user_name} thich post nay'
        params = {
            'user_id': 1,
            'post_id': 2,
        }
        template = NotificationTemplateFactory(content_en=content_en, content_vi=content_vi)

        content = template.get_format_content(params)
        self.assertEqual(content, content_en)

    def test_notification_template_format_redirect_url(self):
        redirect = 'user/{user_id}/post/{post_id}/'
        params = {
            'user_id': 1,
            'post_id': 2,
        }
        template = NotificationTemplateFactory(redirect=redirect)

        redirect_format = template.get_redirect_url(params)
        self.assertEqual(redirect_format, 'user/1/post/2/')

    def test_notification_template_should_return_default_redirect_url_if_missing_params(self):
        redirect = 'user/{user_id}/post/{post_id}/'
        params = {
            'user_id': 1,
        }
        template = NotificationTemplateFactory(redirect=redirect)

        redirect_format = template.get_redirect_url(params)
        self.assertEqual(redirect_format, redirect)
