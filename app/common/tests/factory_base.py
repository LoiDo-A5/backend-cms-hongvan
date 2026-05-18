import factory


class FactoryBase(factory.django.DjangoModelFactory):
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        cls._original_params = kwargs
        return super()._create(model_class, *args, **kwargs)
