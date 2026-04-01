CATEGORY_MAPPING = {
    'painting': 'P',
    'sculpture': 'S',
}

NULL_VALUE = 'NULL'


def get_category_code(category):
    return CATEGORY_MAPPING.get(category, category[:1].upper() if category else NULL_VALUE)


def get_name_code(obj, length=3):
    if not obj or not hasattr(obj, 'name') or not obj.name:
        return NULL_VALUE
    return obj.name


def get_subjects_code(subjects):
    if not subjects or not subjects.exists():
        return NULL_VALUE
    first_subject = subjects.first()
    return first_subject.name if first_subject and hasattr(first_subject, 'name') else NULL_VALUE


def get_year_code(year_created):
    return str(year_created) if year_created else NULL_VALUE


def get_artist_name_code(artwork):
    artist_sources = [
        (artwork.artist, 'legal_name'),
        (artwork.artist_artwork, 'artist_name'),
    ]

    for source, attr in artist_sources:
        if source and hasattr(source, attr) and getattr(source, attr):
            return getattr(source, attr).replace(' ', '').upper()

    return NULL_VALUE


def get_artwork_id_code(artwork_id):
    return str(artwork_id)


def generate_inventory_code(artwork):
    parts = [
        get_category_code(artwork.category),
        get_subjects_code(artwork.subjects),
        get_name_code(artwork.medium),
        get_year_code(artwork.year_created),
        get_artist_name_code(artwork),
        get_artwork_id_code(artwork.id),
    ]
    return '-'.join(parts)
