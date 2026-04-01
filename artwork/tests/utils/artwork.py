from artwork.factories.style_artwork import StyleArtworkFactory
from artwork.factories.subject_artwork import SubjectArtworkFactory
from artwork.factories.medium_artwork import MediumArtworkFactory
from faker import Faker

faker = Faker()


def create_data(user_id, **overrides):
    style = StyleArtworkFactory()
    subject = SubjectArtworkFactory()
    medium = MediumArtworkFactory()
    subject2 = SubjectArtworkFactory()

    size_data = {
        'length': faker.random_int(min=1, max=1000) / 10.0,
        'width': faker.random_int(min=1, max=1000) / 10.0,
        'height': faker.random_int(min=1, max=1000) / 10.0,
        'depth': faker.random_int(min=1, max=1000) / 10.0,
        'weight': faker.random_int(min=1, max=10000) / 10.0,
    }
    images = [
        'image_1.png',
        'image_2.png',
    ]

    data = {
        'title': faker.sentence(),
        'description': faker.paragraph(),
        'category': 'painting',
        'size': size_data,
        'images': images,
        'status': 'sold',
        'is_public': True,
        'is_hide_price': False,
        'currency': 'vnd',
        'price': '1000000',
        'note': faker.paragraph(),
        'year_created': 2008,
        'total_edition': 1,
        'location': None,
        'owner': user_id,
        'style': {
            'id': style.id,
            'name': style.name,
            'category': style.category,
        },
        'subject': {
            'id': subject.id,
            'name': subject.name,
            'category': subject.category,
        },
        'medium': {
            'id': medium.id,
            'name': medium.name,
            'category': medium.category,
        },
        'subjects': [subject2.id],
    }

    data.update(overrides)
    return data
