from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0003_project_section_background_color_and_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='section_background_color',
            field=models.CharField(blank=True, default=None, max_length=7, null=True),
        ),
    ]