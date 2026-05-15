from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_alter_project_section_background_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='project_video',
            field=models.FileField(blank=True, null=True, upload_to='projects/videos/'),
        ),
    ]
