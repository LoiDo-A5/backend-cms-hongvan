import factory
from common.tests.factory_base import FactoryBase

from core.accounts.models import Notification
from core.accounts.factories.user import UserFactory
from core.accounts.factories.notification_template import NotificationTemplateFactory


class NotificationFactory(FactoryBase):
    class Meta:
        model = Notification

    template = factory.SubFactory(NotificationTemplateFactory)
    user = factory.SubFactory(UserFactory)
