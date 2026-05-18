from io import BytesIO

from PIL import Image
from celery import shared_task
from django.core.files.storage import default_storage


@shared_task
def make_thumbnail(image_path, widths):
    image_fp = default_storage.open(image_path)
    im = Image.open(image_fp)

    for width in widths:
        output = BytesIO()
        output.name = image_path.split('/')[-1]
        new_img = im.resize((width, int(im.size[1] * width / im.size[0])))
        new_img.save(output, new_img.format, quality=90)
        output.seek(0)

        name = image_path  # type: str
        if '/' in name:
            path, filename = name.rsplit('/', 1)
            name = '/'.join([path, f'w{width}', filename])
        else:
            name = '/'.join([f'w{width}', name])
        default_storage.save(name, output)
