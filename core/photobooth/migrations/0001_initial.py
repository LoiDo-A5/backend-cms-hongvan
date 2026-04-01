# Generated manually for core.photobooth

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CapturePackage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(help_text='Mã cố định, ví dụ: economy, basic, premium', max_length=64, unique=True)),
                ('name', models.CharField(max_length=120)),
                ('amount_vnd', models.PositiveIntegerField(help_text='Số tiền VND (vd: 59000)')),
                ('print_count', models.PositiveSmallIntegerField(default=1, help_text='Số ảnh in trong gói')),
                ('include_online_file', models.BooleanField(default=True, verbose_name='Nhận file online')),
                ('description_line_1', models.CharField(max_length=255)),
                ('description_line_2', models.CharField(blank=True, max_length=255)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Gói chụp',
                'verbose_name_plural': 'Gói chụp',
                'db_table': 'photobooth_capture_package',
                'ordering': ['sort_order', 'id'],
            },
        ),
    ]
