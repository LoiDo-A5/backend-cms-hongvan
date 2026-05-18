from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0002_project_content_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='section_background_color',
            field=models.CharField(blank=True, default='#030303', max_length=7),
        ),
        migrations.AddField(
            model_name='project',
            name='section_background_mode',
            field=models.CharField(choices=[('color', 'Màu nền'), ('image', 'Ảnh nền')], default='color', max_length=16),
        ),
    ]