from .check_import_all import check_missing


def ignore_abstract_file(filename):
    with open(filename) as f:
        content = f.read()

    meta_count = content.count('class Meta')
    abstract_count = content.count('abstract = True')
    class_count = content.count('class ')
    if meta_count == abstract_count and 2 * meta_count == class_count:
        return True


check_missing('models', ignore_func=ignore_abstract_file)
