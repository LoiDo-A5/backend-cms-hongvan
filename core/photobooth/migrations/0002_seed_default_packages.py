from django.db import migrations


def seed_packages(apps, schema_editor):
    CapturePackage = apps.get_model('photobooth', 'CapturePackage')
    defaults = [
        {
            'code': 'economy',
            'name': 'Tiết kiệm',
            'amount_vnd': 59000,
            'print_count': 1,
            'description_line_1': 'In 1 ảnh chất lượng cao',
            'description_line_2': 'Nhận file ảnh online',
            'sort_order': 10,
        },
        {
            'code': 'basic',
            'name': 'Cơ bản',
            'amount_vnd': 79000,
            'print_count': 2,
            'description_line_1': 'In 2 ảnh chất lượng cao',
            'description_line_2': 'Nhận file ảnh online',
            'sort_order': 20,
        },
        {
            'code': 'premium',
            'name': 'Cao cấp',
            'amount_vnd': 99000,
            'print_count': 3,
            'description_line_1': 'In 3 ảnh chất lượng cao',
            'description_line_2': 'Nhận file ảnh online',
            'sort_order': 30,
        },
    ]
    for row in defaults:
        CapturePackage.objects.update_or_create(
            code=row['code'],
            defaults={
                'name': row['name'],
                'amount_vnd': row['amount_vnd'],
                'print_count': row['print_count'],
                'include_online_file': True,
                'description_line_1': row['description_line_1'],
                'description_line_2': row['description_line_2'],
                'sort_order': row['sort_order'],
                'is_active': True,
            },
        )


def unseed_packages(apps, schema_editor):
    CapturePackage = apps.get_model('photobooth', 'CapturePackage')
    CapturePackage.objects.filter(code__in=('economy', 'basic', 'premium')).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('photobooth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_packages, unseed_packages),
    ]
