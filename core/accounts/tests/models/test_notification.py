from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.notification_template import NotificationTemplateFactory
from core.accounts.factories.notification import NotificationFactory


class NotificationTest(TestCase):
    def test_notification_content(self):
        content_en = '{user_name} like this post'
        content_vi = '{user_name} thich post nay'
        redirect = 'user/{user_id}/post/{post_id}/'
        params = {
            'user_name': 'John',
            'user_id': 1,
            'post_id': 2,
        }
        template = NotificationTemplateFactory(content_en=content_en, content_vi=content_vi, redirect=redirect)
        notification = NotificationFactory(template=template, params=params)

        self.assertEqual(notification.content_en, 'John like this post')
        self.assertEqual(notification.content_vi, 'John thich post nay')
        self.assertEqual(notification.redirect_url, 'user/1/post/2/')

    def test_should_response_default_url_if_not_pass_params(self):
        content = '{user_name} like this post'
        redirect = 'user/{user_id}/post/{post_id}/'
        template = NotificationTemplateFactory(content_en=content, redirect=redirect)
        notification = NotificationFactory(template=template)

        self.assertEqual(notification.content_en, content)
        self.assertEqual(notification.redirect_url, redirect)

    def test_should_response_empty_string_if_not_has_template(self):
        notification = NotificationFactory(template=None)

        self.assertEqual(notification.content_en, '')
        self.assertEqual(notification.redirect_url, '')
