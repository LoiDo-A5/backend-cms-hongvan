import factory

from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory
from core.projects.models import Project


class ProjectFactory(FactoryBase):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f'Dự án {n}')
    website_card_title = factory.LazyAttribute(lambda obj: obj.name)
    website_card_content = 'Dự án về bảo tồn di sản và trải nghiệm số.'
    hero_title = factory.LazyAttribute(lambda obj: obj.name)
    hero_content = 'Nội dung ngắn cho hero section.'
    features = factory.LazyFunction(list)
    accordion_items = factory.LazyFunction(list)
    is_visible = True
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute('created_by')